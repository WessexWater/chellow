package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
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

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = (Element) super.toXML(doc);
		element.setAttribute("serial-number", serialNumber);
		return element;
	}
}
