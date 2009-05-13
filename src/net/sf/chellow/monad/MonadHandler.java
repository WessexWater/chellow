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

import java.io.IOException;
import java.util.Properties;
import java.util.logging.ErrorManager;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.LogRecord;

import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.MimeMessage;

public class MonadHandler extends Handler {
	private MonadContextParameters contextParams;

	private Formatter defaultFormatter = new MonadFormatter();

	public MonadHandler(MonadContextParameters contextParams)
			throws IOException {
		this.contextParams = contextParams;
		setErrorManager(new MonadErrorManager());
	}

	public void publish(LogRecord record) {
		Properties mailProps = new Properties();
		Session session;
		MimeMessage msg;
		String mailHost = contextParams.getMailHost();

		if (mailHost != null) {
			mailProps.setProperty("mail.host", mailHost);
		}
		try {
			Formatter formatter = getFormatter() == null ? defaultFormatter
					: getFormatter();
			session = Session.getInstance(mailProps, null);
			msg = new MimeMessage(session);
			msg.setFrom(contextParams.getFrom());
			msg.setRecipients(MimeMessage.RecipientType.TO, contextParams
					.getTo());
			msg.setText(formatter.format(record));
			Transport.send(msg);
		} catch (Exception e) {
			reportError("MonadHandler error: " + e.toString(), e,
					ErrorManager.GENERIC_FAILURE);
		}
	}

	public void close() {
	}

	public void flush() {
	}
}
