package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class BadRequestException extends HttpException {
	private static final long serialVersionUID = 1L;

	public BadRequestException() throws InternalException {
		this(null, null);
	}
	
	public BadRequestException(String message) throws InternalException {
		this(null, message);
	}
	
	public BadRequestException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_BAD_REQUEST, doc, message, null, null);
	}
}
