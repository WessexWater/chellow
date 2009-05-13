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

import javax.mail.internet.*;
import javax.servlet.*;

public class MonadContextParameters {
	static private final String PARAMETER_LOG_EMAIL_TO = "monad.log.email.to";

	static private final String PARAMETER_LOG_EMAIL_FROM = "monad.log.email.from";

	static private final String PARAMETER_MAIL_HOST = "monad.mail.host";

	private InternetAddress[] to;

	private InternetAddress from;

	private String mailHost;

	private ServletContext context;

	public MonadContextParameters(ServletContext context) throws HttpException {
		String mailHostStr;

		if ((this.context = context) == null) {
			throw new IllegalArgumentException("The 'context' "
					+ "parameter must not be null.");
		}
		mailHostStr = context.getInitParameter(PARAMETER_MAIL_HOST);
		try {
			from = new InternetAddress(
					getRequiredParameter(PARAMETER_LOG_EMAIL_FROM));
			to = InternetAddress.parse(
					getRequiredParameter(PARAMETER_LOG_EMAIL_TO), true);
			mailHost = mailHostStr;

		} catch (AddressException e) {
			throw new DeployerException("Invalid email address in "
					+ "context initialization parameter :" + e.getMessage());
		}
	}

	private String getRequiredParameter(String parameterName)
			throws HttpException {
		String value;

		value = context.getInitParameter(parameterName);
		if (value == null) {
			throw new DeployerException("The context initialization "
					+ "parameter '" + parameterName + "' does not exist.");
		}
		return value;
	}

	public InternetAddress getFrom() {
		return from;
	}

	public InternetAddress[] getTo() {
		return to;
	}

	/**
	 * @return null if no mail.host
	 */
	public String getMailHost() {
		return mailHost;
	}
}
