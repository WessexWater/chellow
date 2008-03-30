/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import java.net.URI;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class UserException extends Exception {
	private static final long serialVersionUID = 1L;

	static public UserException newBadRequest() throws ProgrammerException {
		return newBadRequest(null, null);
	}

	static public UserException newBadRequest(String message)
			throws ProgrammerException {
		return newBadRequest(null, message);
	}

	static public UserException newBadRequest(Document doc, String message)
			throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_BAD_REQUEST, null, null);
	}

	static public UserException newOk(Document doc) throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_OK, doc, null);
	}

	static public UserException newOk(Document document, String message)
			throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_OK, document,
				new VFMessage(message == null ? "" : message));
	}

	static public UserException newOk(String message)
			throws ProgrammerException {
		return newOk(null, message);
	}

	static public UserException newNotFound() throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_NOT_FOUND, null, null);
	}

	static public UserException newNotFound(String message)
			throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_NOT_FOUND, null,
				new VFMessage(message == null ? "" : message));
	}

	static public UserException newNotImplemented() throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_NOT_IMPLEMENTED, null,
				null);
	}

	static public UserException newMovedPermanently(URI uri)
			throws ProgrammerException {
		UserException userException = new UserException(
				HttpServletResponse.SC_MOVED_PERMANENTLY, null, null);
		userException.setLocationHeader(uri);
		return userException;
	}

	static public UserException newForbidden() throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_FORBIDDEN, null, null);
	}

	static public UserException newMethodNotAllowed()
			throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_METHOD_NOT_ALLOWED,
				null, null);
	}

	static public UserException newInvalidParameter()
			throws ProgrammerException {
		return UserException.newInvalidParameter(null, null);
	}

	static public UserException newInvalidParameter(Document doc)
			throws ProgrammerException {
		return UserException.newInvalidParameter(doc, null);
	}

	static public UserException newInvalidParameter(String message)
			throws ProgrammerException {
		return UserException.newInvalidParameter(null, message);
	}

	static public UserException newInvalidParameter(Document doc, String message)
			throws ProgrammerException {
		return new UserException(418, doc, message == null ? null : new VFMessage(message));
	}

	static public UserException newInvalidParameter(VFMessage message)
			throws ProgrammerException {
		return new UserException(418, null, message);
	}

	static public UserException newUnauthorized() throws ProgrammerException {
		return new UserException(HttpServletResponse.SC_UNAUTHORIZED, null,
				null);
	}

	private Document document;

	private VFMessage message;

	private int statusCode;

	private URI locationHeader;

	public UserException(int statusCode, Document doc, VFMessage message)
			throws ProgrammerException {
		super(message == null ? null : message.toString());
		setStatusCode(statusCode);
		setDocument(doc);
		setVFMessage(message);
	}

	public int getStatusCode() {
		return statusCode;
	}

	public URI getLocationHeader() {
		return locationHeader;
	}

	private void setLocationHeader(URI location) {
		this.locationHeader = location;
	}

	public void setStatusCode(int statusCode) {
		this.statusCode = statusCode;
	}

	public void setDocument(Document doc) throws ProgrammerException {
		this.document = doc == null ? MonadUtils.newSourceDocument() : doc;
	}

	public Document getDocument() {
		return document;
	}

	/*
	 * public void setTemplateName(String templateName) { if (templateName ==
	 * null) { templateName = "message"; } this.templateName = templateName; }
	 * 
	 * public String getTemplateName() { return templateName; }
	 */
	public void setVFMessage(VFMessage message) {
		this.message = message;
	}

	public VFMessage getVFMessage() {
		return message;
	}
}