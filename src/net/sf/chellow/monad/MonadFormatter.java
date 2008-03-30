/*
 
 Copyright 2005 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.monad;

import java.sql.SQLException;
import java.util.logging.*;
import javax.servlet.http.*;

public class MonadFormatter extends XMLFormatter {
	public String format(LogRecord record) {
		Object[] params = record.getParameters();
		Throwable thrown = record.getThrown();

		if (params != null) {
			for (int i = 0; i < params.length; i++) {
				if (params[i] instanceof HttpServletRequest) {
					HttpServletRequest req = (HttpServletRequest) params[i];

					params[i] = "Request: "
							+ req.getRequestURL().toString()
							+ (req.getQueryString() == null ? "" : "?"
									+ req.getQueryString());
				} else if (params[i] instanceof Throwable && thrown == null) {
					record.setThrown((Throwable) params[i]);
				}
			}
		}
		if (thrown != null) {
			String thrownMessage = thrown.getMessage();
			StringBuffer message = new StringBuffer(record.getMessage() + "\n" + thrown.getClass().getCanonicalName() + " ");
			Throwable cause;
			Throwable throwable = thrown;
			if (thrownMessage != null) {
				message.append(thrownMessage);
			}
			while ((cause = throwable.getCause()) != null) {
				thrownMessage = cause.getMessage();
				if (thrownMessage != null) {
					message.append(" -> \n");
					message.append(thrownMessage);
				}
				throwable = cause;
			}
			if (throwable instanceof SQLException) {
				SQLException nextException;
				while ((nextException = ((SQLException) throwable).getNextException()) != null) {
					thrownMessage = nextException.getMessage();
					if (thrownMessage != null) {
						message.append(" -> \n");
						message.append(thrownMessage);
					}
					throwable = nextException;
				}
			}
			record.setThrown(throwable);
			record.setMessage(message.toString());
		}
		return super.format(record);
	}
}