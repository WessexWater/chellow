package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Tpr extends PersistentEntity {
	static public Tpr findTpr(int code) {
		return (Tpr) Hiber.session().createQuery(
				"from Tpr tpr where tpr.code = :code").setInteger("code", code)
				.uniqueResult();
	}

	static public Tpr getTpr(String code) throws UserException,
			ProgrammerException {
		try {
			return getTpr(Integer.parseInt(code));
		} catch (NumberFormatException e) {
			throw UserException.newInvalidParameter("Problem parsing code: "
					+ e.getMessage());
		}
	}

	static public Tpr getTpr(int code) throws UserException,
			ProgrammerException {
		Tpr tpr = findTpr(code);
		if (tpr == null) {
			throw UserException
					.newInvalidParameter("Can't find a TPR with code '" + code
							+ "'.");
		}
		return tpr;
	}

	static public Tpr insertTpr(int code) {
		Tpr tpr = new Tpr(code);
		Hiber.session().save(tpr);
		return tpr;
	}

	static public Tpr getTpr(long id) throws UserException, ProgrammerException {
		Tpr tpr = (Tpr) Hiber.session().get(Tpr.class, id);
		if (tpr == null) {
			throw UserException.newNotFound();
		}
		return tpr;
	}

	private Set<Ssc> sscs;

	private int code;

	private Set<TprLine> lines;

	public Tpr() {
		setTypeName("tpr");
	}

	public Tpr(int code) {
		setSscs(new HashSet<Ssc>());
		setCode(code);
		setLines(new HashSet<TprLine>());
	}

	public Set<Ssc> getSscs() {
		return sscs;
	}

	void setSscs(Set<Ssc> sscs) {
		this.sscs = sscs;
	}

	int getCode() {
		return code;
	}

	void setCode(int code) {
		this.code = code;
	}

	public Set<TprLine> getLines() {
		return lines;
	}

	void setLines(Set<TprLine> lines) {
		this.lines = lines;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree("sscs").put("lines"), doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public TprLine insertLine(int monthFrom, int monthTo, int dayOfWeekFrom,
			int dayOfWeekTo, int hourFrom, int minuteFrom, int hourTo,
			int minuteTo, boolean isGmt) throws UserException,
			ProgrammerException {
		TprLine line = new TprLine(this, monthFrom, monthTo, dayOfWeekFrom,
				dayOfWeekTo, hourFrom, minuteFrom, hourTo, minuteTo, isGmt);
		lines.add(line);
		return line;
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttribute("code", Integer.toString(code));
		return element;
	}

	public String toString() {
		return Integer.toString(code);
	}

}
