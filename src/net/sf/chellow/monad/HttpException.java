/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

package net.sf.chellow.monad;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.URI;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class HttpException extends Exception implements XmlDescriber {
	public static String getStackTraceString(Throwable e) {
		StringWriter writer = new StringWriter();
		PrintWriter printWriter = new PrintWriter(writer);
		Throwable cause = e.getCause();
		e.printStackTrace(printWriter);
		if (cause != null) {
			printWriter.write("\n------------\nNested exception:\n");
			cause.printStackTrace(printWriter);
		}
		return writer.toString();
	}
	
	private static final long serialVersionUID = 1L;

	private Document document;

	private int statusCode;

	private URI location;

	public HttpException(int statusCode, Document doc, String message,
			URI location, Throwable cause) throws InternalException {
		super(message, cause);
		setStatusCode(statusCode);
		setDocument(doc);
		setLocation(location);
	}

	public int getStatusCode() {
		return statusCode;
	}

	public URI getLocation() {
		return location;
	}

	private void setLocation(URI location) {
		this.location = location;
	}

	public void setStatusCode(int statusCode) {
		this.statusCode = statusCode;
	}

	public void setDocument(Document doc) throws InternalException {
		if (doc == null) {
			doc = MonadUtils.newSourceDocument();
		}
		this.document = doc;
	}

	public Document getDocument() {
		return document;
	}
	
	public Element toXml(Document doc) {
		return new MonadMessage(getMessage()).toXml(doc);
	}
	
	public Element toXml(Document doc, XmlTree tree) {
		return toXml(doc);
	}
	
	public String getStackTraceString() {
		return getStackTraceString(this);
	}
}