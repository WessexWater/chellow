package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MeterTimeswitches implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("meter-timeswitches");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MeterTimeswitches() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUrlId())
				.append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		for (MeterTimeswitch mtc : (List<MeterTimeswitch>) Hiber.session()
				.createQuery(
						"select mtc from MeterTimeswitch mtc left outer join mtc.dso dso order by mtc.code, dso.code")
				.list()) {
			source.appendChild(mtc.toXml(doc, new XmlTree("dso")));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public MeterTimeswitch getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		return MeterTimeswitch.getMeterTimeswitch(Long.parseLong(uriId
				.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}
}