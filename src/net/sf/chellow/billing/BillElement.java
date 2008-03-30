package net.sf.chellow.billing;

import java.util.ArrayList;
import java.util.List;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDouble;
import net.sf.chellow.monad.types.MonadString;

public class BillElement implements XmlDescriber {
	private String name;

	private double cost;

	private String working;

	private List<BillElement> subElements = new ArrayList<BillElement>();

	public BillElement(String name, double cost, String working) {
		this.name = name;
		this.cost = cost;
		this.working = working;
	}

	public String getName() {
		return name;
	}

	public double getCost() {
		return cost;
	}

	public String getWorking() {
		return working;
	}

	public List<BillElement> getSubElements() {
		return subElements;
	}

	public void addSubElement(BillElement billElement) {
		subElements.add(billElement);
	}
	
	public void addSubElement(String name, double cost, String working) {
		subElements.add(new BillElement(name, cost, working));
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException, DesignerException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException, DesignerException {
		Element element = doc.createElement("bill-element");

		element.setAttributeNode(MonadString.toXml(doc, "name", name));
		element.setAttributeNode(MonadDouble.toXml(doc, "cost", cost));
		element.setAttributeNode(MonadString.toXml(doc, "working", working));
		for (BillElement billElement : getSubElements()) {
			element.appendChild(billElement.toXML(doc));
		}
		return element;
	}
}
