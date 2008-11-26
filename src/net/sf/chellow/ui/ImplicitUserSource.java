package net.sf.chellow.ui;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.User;

public class ImplicitUserSource {
	static public User getUser(Invocation inv) throws HttpException {
		User user = null;
		Configuration configuration = Configuration.getConfiguration();
		String emailAddressString = configuration.getProperty("ip"
				+ inv.getRequest().getRemoteAddr().replace(".", "-"));
		if (emailAddressString != null) {
			user = User
					.findUserByEmail(new EmailAddress(emailAddressString.trim()));
		}
		return user;
	}
}