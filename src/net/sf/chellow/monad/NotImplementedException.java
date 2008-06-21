package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class NotImplementedException extends HttpException {
	private static final long serialVersionUID = 1L;

	public NotImplementedException() throws InternalException {
		this(null, null);
	}
	
	public NotImplementedException(String message) throws InternalException {
		this(null, message);
	}
	
	public NotImplementedException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_NOT_IMPLEMENTED, doc, message, null, null);
	}
}
