/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

package net.sf.chellow.monad.types;

import java.lang.reflect.InvocationTargetException;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public abstract class MonadObject implements MonadValidatable, XmlDescriber {
	private String label = null;

	// private String typeName = null;

	public MonadObject(String typeName, String label) {
		setLabel(label);
		// this.typeName = typeName;
	}

	public MonadObject(String label) {
		this(null, label);
	}

	public MonadObject() {
	}

	public void setLabel(String label) {
		this.label = label;
	}

	public String getLabel() {
		return label;
	}

	/*
	 * public String getTypeName() { if (typeName == null) { typeName =
	 * this.getClass().getSimpleName(); } return typeName; }
	 * 
	 * protected void setTypeName(String typeName) { this.typeName = typeName; }
	 */
	public Node toXml(Document doc, String elementName) throws HttpException {
		Element element = doc.createElement(elementName);

		if (label != null) {
			element.setAttribute("label", label);
		}
		return element;
	}

	protected void checkNull(Object value, String name) {
		if (value == null) {
			throw new IllegalArgumentException("The argument '" + name
					+ "' must not be null.");
		}
	}

	@SuppressWarnings("unchecked")
	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		Node node = toXml(doc);

		for (String methodBase : tree.keySet()) {
			XmlTree nestedTree = tree.get(methodBase);
			String methodName = "get"
					+ methodBase.substring(0, 1).toUpperCase()
					+ methodBase.substring(1);

			try {
				Object obj = this.getClass()
						.getMethod(methodName, new Class<?>[] {})
						.invoke(this, new Object[] {});
				if (obj != null) {
					if (obj instanceof Set) {
						for (XmlDescriber jt : ((Set<XmlDescriber>) obj)) {
							node.appendChild(describerNode(doc, jt, nestedTree));
						}
					} else if (obj instanceof List) {
						for (XmlDescriber jt : ((List<XmlDescriber>) obj)) {
							node.appendChild(describerNode(doc, jt, nestedTree));
						}
					} else {
						Node newNode = describerNode(doc, (XmlDescriber) obj,
								nestedTree);
						if (node instanceof Element && newNode instanceof Attr) {
							((Element) node).setAttributeNode((Attr) newNode);
						} else {
							node.appendChild(newNode);
						}
					}
				}
			} catch (SecurityException e) {
				throw new InternalException(e);
			} catch (IllegalArgumentException e) {
				throw new InternalException(e);
			} catch (IllegalAccessException e) {
				throw new InternalException(e);
			} catch (InvocationTargetException e) {
				throw new InternalException(e);
			} catch (NoSuchMethodException e) {
				throw new InternalException(e);
			}
		}
		return node;
	}

	private Node describerNode(Document doc, XmlDescriber describer,
			XmlTree tree) throws HttpException {
		return (tree == null) ? describer.toXml(doc) : describer.toXml(doc,
				tree);
	}

	public boolean equals(Object obj) {
		return this.getClass().isInstance(obj);
	}
}
