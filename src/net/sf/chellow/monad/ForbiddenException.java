package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class ForbiddenException extends HttpException {

	private static final long serialVersionUID = 1L;
	public ForbiddenException() throws InternalException {
		this(null, null);
	}
	
	public ForbiddenException(String message) throws InternalException {
		this(null, message);
	}
	
	public ForbiddenException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_FORBIDDEN, doc, message, null, null);
	}
}
