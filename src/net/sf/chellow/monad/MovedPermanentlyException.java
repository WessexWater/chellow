package net.sf.chellow.monad;

import java.net.URI;

import javax.servlet.http.HttpServletResponse;

public class MovedPermanentlyException extends HttpException {
	private static final long serialVersionUID = 1L;
		
	public MovedPermanentlyException(URI location) throws InternalException {
		super(HttpServletResponse.SC_MOVED_PERMANENTLY, null, null, location, null);
	}
}
