/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
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
