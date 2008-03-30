/*
 
 Copyright 2005 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.monad.types;

import java.lang.reflect.InvocationTargetException;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public abstract class MonadObject implements MonadValidatable, XmlDescriber {
	private String label = null;

	private String typeName = null;

	public MonadObject(String typeName, String label) {
		setLabel(label);
		this.typeName = typeName;
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

	public String getTypeName() {
		if (typeName == null) {
			typeName = this.getClass().getSimpleName();
		}
		return typeName;
	}

	protected void setTypeName(String typeName) {
		this.typeName = typeName;
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = doc.createElement(getTypeName());

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
	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException, DesignerException {
		Node node = toXML(doc);

		for (Iterator<String> it = tree.keyIterator(); it.hasNext();) {
			String methodBase = it.next();
			XmlTree nestedTree = tree.get(methodBase);
			String methodName = "get"
					+ methodBase.substring(0, 1).toUpperCase()
					+ methodBase.substring(1);

			try {
				Object obj = this.getClass().getMethod(methodName,
						new Class<?>[] {}).invoke(this, new Object[] {});
				if (obj != null) {
					if (obj instanceof Set) {
						for (XmlDescriber jt : ((Set<XmlDescriber>) obj)) {
							node.appendChild(describerNode(doc,
									jt, nestedTree));
						}
					} else if (obj instanceof List) {
						for (Iterator jt = ((List) obj).iterator(); jt
								.hasNext();) {
							node.appendChild(describerNode(doc,
									(XmlDescriber) jt.next(), nestedTree));
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
				throw new ProgrammerException(e);
			} catch (IllegalArgumentException e) {
				throw new ProgrammerException(e);
			} catch (IllegalAccessException e) {
				throw new ProgrammerException(e);
			} catch (InvocationTargetException e) {
				throw new ProgrammerException(e);
			} catch (NoSuchMethodException e) {
				throw new ProgrammerException(e);
			}
		}
		return node;
	}

	private Node describerNode(Document doc, XmlDescriber describer,
			XmlTree tree) throws ProgrammerException, UserException, DesignerException {
		return (tree == null) ? describer.toXML(doc) : describer.getXML(tree,
				doc);
	}

	public boolean equals(Object obj) {
		return this.getClass().isInstance(obj);
	}
}
