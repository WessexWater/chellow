/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
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
