package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Meter extends PersistentEntity {
	private Supply supply;

	private String serialNumber;

	Meter() {
		setTypeName("meter");
	}

	public Meter(Supply supply, String serialNumber) {
		setSupply(supply);
		setSerialNumber(serialNumber);
	}

	Supply getSupply() {
		return supply;
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	String getSerialNumber() {
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
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws InternalException,
			HttpException {
		Element element = (Element) super.toXml(doc);
		element.setAttribute("serial-number", serialNumber);
		return element;
	}
}
