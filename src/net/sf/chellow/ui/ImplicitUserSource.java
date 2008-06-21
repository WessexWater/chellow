package net.sf.chellow.ui;

import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadUri;

import net.sf.chellow.physical.User;

public class ImplicitUserSource {
	public static final EmailAddress BASIC_USER_EMAIL_ADDRESS;

	static {
		try {
			BASIC_USER_EMAIL_ADDRESS = new EmailAddress("basic-user@localhost");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	static public User getUser(Invocation inv) throws HttpException,
			InternalException {
		User user = null;
		if (ChellowProperties.propertiesExists(new MonadUri("/"),
				"implicit-user-source.properties")) {
			ChellowProperties properties = new ChellowProperties(new MonadUri(
					"/"), "implicit-user-source.properties");
			String emailAddressString = properties.getProperty("ip"
					+ inv.getRequest().getRemoteAddr().replace(".", "-"));
			if (emailAddressString != null) {
				user = User
						.findUserByEmail(new EmailAddress(emailAddressString));
			}
		}
		if (user == null) {
			user = User.findUserByEmail(BASIC_USER_EMAIL_ADDRESS);
			if (user == null) {
				throw new InternalException("The basic user '"
						+ BASIC_USER_EMAIL_ADDRESS + "' can't be found.");
			}
		}
		return user;
	}
}
