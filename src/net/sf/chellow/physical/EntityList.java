package net.sf.chellow.physical;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

public abstract class EntityList implements Urlable, XmlDescriber {
	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
	
	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}
}
