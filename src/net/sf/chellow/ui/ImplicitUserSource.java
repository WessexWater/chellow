package net.sf.chellow.ui;

import java.io.IOException;
import java.io.StringReader;
import java.util.Properties;

import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.User;

public class ImplicitUserSource {
	static public User getUser(Invocation inv) throws HttpException {
		User user = null;
		Configuration dbVersion = Configuration.getConfiguration();
		String propsString = dbVersion.getImplicitUserProperties();
		if (propsString != null) {
			Properties props = new Properties();
			try {
				props.load(new StringReader(propsString));
			} catch (IOException e) {
				throw new InternalException(e);
			}
			String emailAddressString = props.getProperty("ip"
					+ inv.getRequest().getRemoteAddr().replace(".", "-"));
			if (emailAddressString != null) {
				user = User
						.findUserByEmail(new EmailAddress(emailAddressString));
			}
		}
		if (user == null) {
			user = User.findUserByEmail(User.BASIC_USER_EMAIL_ADDRESS);
			if (user == null) {
				throw new InternalException("The basic user '"
						+ User.BASIC_USER_EMAIL_ADDRESS + "' can't be found.");
			}
		}
		return user;
	}
}