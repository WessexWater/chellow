package net.sf.chellow.billing;

import net.sf.chellow.monad.HttpException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Mop extends Provider {
	public Mop() {
	}
	
	public Element toXml(Document doc) throws HttpException {
		return super.toXml(doc, "mop");
	}
}
