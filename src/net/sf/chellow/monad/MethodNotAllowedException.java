package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class MethodNotAllowedException extends HttpException {

	private static final long serialVersionUID = 1L;

	public MethodNotAllowedException() throws InternalException {
		this(null, null);
	}
	
	public MethodNotAllowedException(String message) throws InternalException {
		this(null, message);
	}
	
	public MethodNotAllowedException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_METHOD_NOT_ALLOWED, doc, message, null, null);
	}
}
