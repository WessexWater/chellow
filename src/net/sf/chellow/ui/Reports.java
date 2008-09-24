package net.sf.chellow.ui;

import java.io.File;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.SortedMap;
import java.util.TreeMap;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Reports extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("reports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Reports() {
	}

	@SuppressWarnings("unchecked")
	private Map<Long, Report> getReports() throws HttpException {
		SortedMap<Long, Report> reports = new TreeMap<Long, Report>();
		if (Monad.getConfigDir() != null) {
			File reportsPath = new File(Monad.getConfigDir().toString()
					+ getUri().toString().replace("/", File.separator));
			File[] fileListing = reportsPath.listFiles();
			if (fileListing != null) {
				for (File file : fileListing) {
					if (file.isDirectory() && !file.getName().equals("default")) {
						Long id = new Long(Long.parseLong(file.getName()));
						MonadUri uri = new MonadUri(reportsPath.toString()
								.substring(
										Monad.getConfigDir().toString()
												.length()).replace("\\", "/")
								+ "/" + file.getName() + "/");
						reports.put(id, new Report(this, id, uri));
					}
				}
			}
			reportsPath = new File(Monad.getConfigDir().toString()
					+ Chellow.ORGANIZATIONS_INSTANCE.getUri().toString()
							.replace("/", File.separator) + "default"
					+ File.separator + "reports");
			fileListing = reportsPath.listFiles();
			if (fileListing != null) {
				for (File file : fileListing) {
					if (file.isDirectory() && !file.getName().equals("default")) {
						Long id = new Long(Long.parseLong(file.getName()));
						MonadUri uri = new MonadUri(reportsPath.toString()
								.substring(
										Monad.getConfigDir().toString()
												.length()).replace("\\", "/")
								+ "/" + file.getName() + "/");
						reports.put(id, new Report(this, id, uri));
					}
				}
			}
		}
		Set<String> allPaths = new HashSet<String>();
		Set<String> paths = Monad.getContext().getResourcePaths(
				Monad.getConfigPrefix() + getUri().toString());
		if (paths != null) {
			allPaths.addAll(paths);
		}
		paths = Monad.getContext().getResourcePaths(
				Monad.getConfigPrefix()
						+ Chellow.ORGANIZATIONS_INSTANCE.getUri().toString()
						+ "default/reports/");
		allPaths.addAll(paths);
		for (String path : allPaths) {
			if (path.endsWith("/") && !path.endsWith("/default/")) {
				String idPath = path.substring(0, path.length() - 1);
				Long id = new Long(Long.parseLong(idPath.substring(idPath
						.lastIndexOf("/") + 1, idPath.length())));
				MonadUri reportUri = new MonadUri(path.substring(Monad
						.getConfigPrefix().length()));
				reports.put(id, new Report(this, id, reportUri));
			}
		}
		return reports;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportsElement = toXml(doc);
		
		source.appendChild(reportsElement);
		for (Report report : (List<Report>) Hiber.session().createQuery(
				"from Report report order by report.id").list()) {
			reportsElement.appendChild(report.toXml(doc));
		}
		return doc;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(URI_ID).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		String name = inv.getString("name");
		String script = inv.getString("script");
		
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		String template = null;
		if (inv.hasParameter("has-template")) { 
		template = inv.getString("template");
		}
		
		/*
		 * MonadString name = inv.getMonadString("name"); Document doc =
		 * MonadUtilsUI.newSourceDocument();
		 * 
		 * if (!inv.isValid()) { inv.sendInvalidParameter(doc); } Role role =
		 * Role.insertRole(name); User user = inv.getUser();
		 * user.userRole(user).insertPermission(role.getUri().toString(), new
		 * Invocation.HttpMethod[] { Invocation.HttpMethod.GET,
		 * Invocation.HttpMethod.POST }); Hiber.close();
		 * inv.sendCreated(role.getUri());
		 */
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return getReports().get(Long.parseLong(uriId.toString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("reports");
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}
}
