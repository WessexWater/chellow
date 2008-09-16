package net.sf.chellow.physical;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class ReadType extends PersistentEntity {
	public static final char TYPE_CHANGE_OF_SUPPLIER = 'A';

	public static final char TYPE_CUSTOMER = 'C';

	public static final char TYPE_DEEMED = 'D';

	public static final char TYPE_FINAL = 'F';

	public static final char TYPE_INITIAL = 'I';
	public static final char TYPE_MAR = 'M';
	public static final char TYPE_OLD_SUPPLIERS_ESTIMATED = 'O';
	public static final char TYPE_PPMIP = 'P';
	public static final char TYPE_DC_MANUAL = 'Q';
	public static final char TYPE_ROUTINE = 'R';
	public static final char TYPE_SPECIAL = 'S';
	public static final char TYPE_TEST = 'T';
	public static final char TYPE_WITHDRAWN = 'W';
	public static final char TYPE_CHANGE_OF_TENANCY = 'Z';
	public static final char TYPE_ESTIMATE = 'E';
	

	static public ReadType getReadType(Long id) throws HttpException {
		ReadType readType = (ReadType) Hiber.session().get(
				ReadType.class, id);
		if (readType == null) {
			throw new NotFoundException();
		}
		return readType;
	}

	static public ReadType getReadType(char code) throws HttpException {
		ReadType type = (ReadType) Hiber.session().createQuery(
				"from ReadType type where type.code = :code").setCharacter(
				"code", code).uniqueResult();
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public ReadType getReadType(String code) throws HttpException {
		code = code.trim();
		int length = code.length();
		if (length > 1 || length < 1) {
			throw new UserException("The read type can only be a single character.");
		}
		return getReadType(code.charAt(0));
	}
	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add read types.");
		Mdd mdd = new Mdd(sc, "ReadType", new String[] {
				"Code", "Description" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			ReadType type = new ReadType(values[0].charAt(0), values[1]);
			Hiber.session().save(type);
			Hiber.close();
		}
		Debug.print("Finished adding read types.");
	}

	private char code;
	private String description;

	public ReadType() {
	}

	public ReadType(char code, String description) {
		this.code = code;
		this.description = description;
	}

	public char getCode() {
		return code;
	}

	public void setCode(char code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}

	@Override
	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "read-type");

		element.setAttribute("code", String.valueOf(code));
		element.setAttribute("description", description);
		return element;
	}
}