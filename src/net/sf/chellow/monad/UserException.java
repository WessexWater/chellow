package net.sf.chellow.monad;

import org.w3c.dom.Document;

public class UserException extends HttpException {

	private static final long serialVersionUID = 1L;

	public UserException() throws InternalException {
		this(null, null);
	}
	
	public UserException(String message) throws InternalException {
		this(null, message);
	}
	
	public UserException(Document doc) throws InternalException {
		this(doc, null);
	}
	
	public UserException(Document doc, String message) throws InternalException {
		super(418, doc, message, null, null);
	}

}
