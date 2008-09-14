package net.sf.chellow.billing;

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class VirtualBill implements XmlDescriber {
	private String name;

	private double cost;

	private String working;

	private List<VirtualBill> subBills = new ArrayList<VirtualBill>();

	public VirtualBill(String name, double cost, String working) {
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

	public List<VirtualBill> getSubElements() {
		return subBills;
	}

	public void addSubBill(VirtualBill bill) {
		subBills.add(bill);
	}
	
	public void addSubBill(String name, double cost, String working) {
		subBills.add(new VirtualBill(name, cost, working));
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("virtual-bill");

		element.setAttribute("name", name);
		element.setAttribute("cost", Double.toString(cost));
		element.setAttribute("working", working);
		for (VirtualBill bill : getSubElements()) {
			element.appendChild(bill.toXml(doc));
		}
		return element;
	}
}