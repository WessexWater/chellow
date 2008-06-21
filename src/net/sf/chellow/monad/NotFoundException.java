package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class NotFoundException extends HttpException {
	private static final long serialVersionUID = 1L;

	public NotFoundException() throws InternalException {
		this(null, null);
	}
	
	public NotFoundException(String message) throws InternalException {
		this(null, message);
	}
	
	public NotFoundException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_NOT_FOUND, doc, message, null, null);
	}
}
