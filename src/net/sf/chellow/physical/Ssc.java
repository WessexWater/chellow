package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Ssc extends PersistentEntity {
	public static Ssc insertSsc(int code, String tprs)
			throws InternalException, HttpException {
		Ssc ssc = new Ssc(code, tprs);
		Hiber.session().save(ssc);
		Hiber.flush();
		return ssc;
	}

	static public Ssc getSsc(String code) throws HttpException,
			InternalException {
		try {
			return getSsc(Integer.parseInt(code.trim()));
		} catch (NumberFormatException e) {
			throw new UserException("Problem parsing code: "
					+ e.getMessage());
		}
	}

	public static Ssc getSsc(int code) throws HttpException,
			InternalException {
		Ssc ssc = (Ssc) Hiber.session().createQuery(
				"from Ssc ssc where ssc.code = :code").setInteger("code", code)
				.uniqueResult();
		if (ssc == null) {
			throw new UserException
					("There isn't an SSC with code: "
							+ code + ".");
		}
		return ssc;
	}

	public static Ssc getSsc(long id) throws HttpException, InternalException {
		Ssc ssc = (Ssc) Hiber.session().get(Ssc.class, id);
		if (ssc == null) {
			throw new UserException
					("There isn't an SSC with id: " + id
							+ ".");
		}
		return ssc;
	}

	private SscCode code;

	private Set<MpanTop> mpanTops;

	private Set<Tpr> tprs;

	public Ssc() {
	}

	public Ssc(int code, String tprString) throws InternalException,
			HttpException {
		setCode(new SscCode(code));
		setTprs(new HashSet<Tpr>());
		if (tprString != null && tprString.trim().length() > 0) {
			for (String tprCode : tprString.split(",")) {
				Tpr tpr = Tpr.getTpr(tprCode);
				tprs.add(tpr);
			}
		}
	}

	public SscCode getCode() {
		return code;
	}

	void setCode(SscCode code) {
		this.code = code;
	}

	public Set<MpanTop> getMpanTops() {
		return mpanTops;
	}

	void setMpanTops(Set<MpanTop> mpanTops) {
		this.mpanTops = mpanTops;
	}

	public Set<Tpr> getTprs() {
		return tprs;
	}

	void setTprs(Set<Tpr> tprs) {
		this.tprs = tprs;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("tprs")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws InternalException,
			HttpException {
		setTypeName("ssc");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code.toString());
		return element;
	}
}
