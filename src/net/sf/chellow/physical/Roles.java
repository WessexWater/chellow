package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.NewRoleForm;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Roles implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("roles");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Roles() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element rolesElement = (Element) toXml(doc);
		source.appendChild(rolesElement);
		for (Role role : (List<Role>) Hiber.session().createQuery(
				"from Role role").list()) {
			rolesElement.appendChild(role.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		String name = inv.getString("name");
		Document doc = MonadUtils.newSourceDocument();

		if (!inv.isValid()) {
			throw new UserException(doc);
		}
		Role role = Role.insertRole(inv.getUser(), name);
		Hiber.commit();
		inv.sendCreated(role.getUri());
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		Urlable urlable = null;
		if (NewRoleForm.URI_ID.equals(uriId)) {
			urlable = new NewRoleForm();
		} else {
			urlable = (Role) Hiber.session().createQuery(
					"from Role role where role.id = :roleId").setLong("roleId",
					Long.parseLong(uriId.getString())).uniqueResult();
		}
		return urlable;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		return doc.createElement("roles");
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
