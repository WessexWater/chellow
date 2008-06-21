package net.sf.chellow.monad;

import javax.servlet.http.HttpServletResponse;

import org.w3c.dom.Document;

public class UnauthorizedException extends HttpException {

	private static final long serialVersionUID = 1L;

	public UnauthorizedException() throws InternalException {
		this(null, null);
	}
	
	public UnauthorizedException(String message) throws InternalException {
		this(null, message);
	}
	
	public UnauthorizedException(Document doc, String message) throws InternalException {
		super(HttpServletResponse.SC_UNAUTHORIZED, doc, message, null, null);
	}

}
