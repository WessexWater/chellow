package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
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

	static public Tpr getTpr(String code) throws InternalException, UserException {
		try {
			return getTpr(Integer.parseInt(code));
		} catch (NumberFormatException e) {
			throw new UserException("Problem parsing code: "
					+ e.getMessage());
		}
	}

	static public Tpr getTpr(int code) throws InternalException, UserException {
		Tpr tpr = findTpr(code);
		if (tpr == null) {
			throw new UserException("Can't find a TPR with code '" + code
							+ "'.");
		}
		return tpr;
	}

	static public Tpr insertTpr(int code) {
		Tpr tpr = new Tpr(code);
		Hiber.session().save(tpr);
		return tpr;
	}

	static public Tpr getTpr(long id) throws NotFoundException, InternalException {
		Tpr tpr = (Tpr) Hiber.session().get(Tpr.class, id);
		if (tpr == null) {
			throw new NotFoundException();
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

	public Urlable getChild(UriPathElement uriId) throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("sscs").put("lines")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public TprLine insertLine(int monthFrom, int monthTo, int dayOfWeekFrom,
			int dayOfWeekTo, int hourFrom, int minuteFrom, int hourTo,
			int minuteTo, boolean isGmt) throws HttpException,
			InternalException {
		TprLine line = new TprLine(this, monthFrom, monthTo, dayOfWeekFrom,
				dayOfWeekTo, hourFrom, minuteFrom, hourTo, minuteTo, isGmt);
		lines.add(line);
		return line;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", Integer.toString(code));
		return element;
	}

	public String toString() {
		return Integer.toString(code);
	}

}
