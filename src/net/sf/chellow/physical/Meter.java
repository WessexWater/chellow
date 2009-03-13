package net.sf.chellow.physical;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Meter extends PersistentEntity {
	private Supply supply;

	private String serialNumber;

	Meter() {
	}

	public Meter(Supply supply, String serialNumber) {
		setSupply(supply);
		setSerialNumber(serialNumber);
	}

	public Supply getSupply() {
		return supply;
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public String getSerialNumber() {
		return serialNumber;
	}

	void setSerialNumber(String serialNumber) {
		this.serialNumber = serialNumber;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "meter");
		element.setAttribute("serial-number", serialNumber);
		return element;
	}
}
