package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class OkException extends HttpException {
	private static final long serialVersionUID = 1L;

	public OkException() throws InternalException {
		this(null, null);
	}
	
	public OkException(String message) throws InternalException {
		this(null, message);
	}
	
	public OkException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_OK, doc, message, null, null);
	}
}
