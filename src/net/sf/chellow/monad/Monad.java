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

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.ConsoleHandler;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.mail.internet.AddressException;
import javax.mail.internet.InternetAddress;
import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Result;
import javax.xml.transform.Source;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerConfigurationException;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.URIResolver;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Monad extends HttpServlet implements Urlable {
	static private String contextPath;

	static private Urlable urlableRoot;

	static public String getContextPath() {
		return contextPath;
	}

	static public Urlable getUrlableRoot() {
		return urlableRoot;
	}

	private static final MonadUri URI;

	static {
		try {
			URI = new MonadUri("/");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private String realmName;

	static private final String CONFIG_PREFIX = "/WEB-INF/default-config";

	static private final String DEBUG_FILE_NAME = "debug";

	protected Class<Invocation> invocationClass;

	// protected static final int PERMISSION_SESSION = 1;

	// private static final Class[] invocationConstructorTypes = {
	// HttpServletRequest.class, HttpServletResponse.class, String.class };

	//private Class<Object>[] ARG_TYPES = new Class[1];

	/*
	 * private Map<String, List<DesignerMethodFilter>> designerMethods = new
	 * HashMap<String, List<DesignerMethodFilter>>();
	 * 
	 * private Class thisClass;
	 */
	// private Constructor invocationConstructor;
	static private ServletContext context;

	static private File CONFIG_DIR = null;

	private String templateDirName;

	static protected Logger logger = Logger
			.getLogger("uk.org.tlocke.theelected");

	// private HibernateUtil hibernateUtil = null;

	static public ServletContext getContext() {
		return context;
	}

	static public void setContext(ServletContext context) {
		Monad.context = context;
	}

	static public File getConfigDir() {
		return CONFIG_DIR;
	}

	static public String getConfigPrefix() {
		return CONFIG_PREFIX;
	}

	public Monad() {
		urlableRoot = this;
		// thisClass = this.getClass();
		invocationClass = getInvocationClass();
		//ARG_TYPES[0] = invocationClass;
		Handler consoleHandler = new ConsoleHandler();
		consoleHandler.setFormatter(new MonadFormatter());
		logger.addHandler(consoleHandler);
	}

	protected Class<Invocation> getInvocationClass() {
		return Invocation.class;
	}

	public String getRealmName() {
		return realmName;
	}

	protected void setRealmName(String realmName) {
		this.realmName = realmName;
	}

	protected void setTemplateDirName(String templateDirName) {
		this.templateDirName = templateDirName;
	}

	public String getTemplateDirName() {
		return templateDirName;
	}

	protected void setHibernateUtil(Hiber hibernateUtil) {
		// this.hibernateUtil = hibernateUtil;
	}

	public void init(ServletConfig conf) throws ServletException {
		super.init(conf);
		context = conf.getServletContext();

		/*
		 * try { invocationConstructor = invocationClass
		 * .getConstructor(invocationConstructorTypes); } catch
		 * (NoSuchMethodException e) { logger.logp(Level.SEVERE,
		 * "uk.org.tlocke.monad.Monad", "init", "Can't initialize servlet", e);
		 * throw new ServletException(e.getMessage()); }
		 */
	}

	/*
	 * protected void addDesignerMethod(String name) throws ProgrammerException {
	 * addDesignerMethod(name, new DesignerMethodFilter[0]); }
	 * 
	 * protected void addDesignerMethod(String name, DesignerMethodFilter[]
	 * filters) throws ProgrammerException { List<DesignerMethodFilter>
	 * filterList = Arrays.asList(filters);
	 * 
	 * try { thisClass.getDeclaredMethod(name, ARG_TYPES); } catch
	 * (NoSuchMethodException e) { Method[] methods =
	 * thisClass.getDeclaredMethods(); StringBuffer buf = new StringBuffer();
	 * 
	 * for (int i = 0; i < methods.length; i += 1) { buf.append("\n" +
	 * methods[i]); } buf.append("\narg types"); for (int i = 0; i <
	 * ARG_TYPES.length; i += 1) { buf.append("\n" + ARG_TYPES[i]); } throw new
	 * ProgrammerException("A method of this name doesn't " + "exist: " +
	 * e.getMessage() + buf + "arg types"); } designerMethods.put(name,
	 * filterList); }
	 */
	protected abstract void checkPermissions(Invocation inv)
			throws InternalException, HttpException;

	@SuppressWarnings("unchecked")
	public void service(HttpServletRequest req, HttpServletResponse res)
			throws IOException, ServletException {
		contextPath = req.getContextPath();
		Invocation inv = null;
		try {
			try {
				Class[] classArray = new Class[] { HttpServletRequest.class,
						HttpServletResponse.class, Monad.class };
				inv = (Invocation) invocationClass.getConstructor(classArray)
						.newInstance(new Object[] { req, res, this });
				String pathInfo = req.getPathInfo();
				if (pathInfo != null && !pathInfo.endsWith("/")) {
					try {
						throw new MovedPermanentlyException(new URI(
								contextPath + req.getPathInfo() + "/"));
					} catch (URISyntaxException e) {
						throw new BadRequestException(e.getMessage());
					}
				}
				checkPermissions(inv);
				Urlable urlable = inv.dereferenceUrl();
				if (urlable == null) {
					inv.returnStatic(getServletConfig().getServletContext(),
							pathInfo);
				} else {
					String method = req.getMethod();
					if (method.equals("GET")) {
						urlable.httpGet(inv);
					} else if (method.equals("POST")) {
						urlable.httpPost(inv);
					} else if (method.equals("DELETE")) {
						urlable.httpDelete(inv);
					}
				}
			} catch (ForbiddenException e) {
				inv.sendForbidden();
			} catch (MovedPermanentlyException e) {
				inv.sendMovedPermanently(e.getLocation());
			} catch (NotFoundException e) {
				inv.sendNotFound();
			} catch (OkException e) {
				if (e.getMessage() != null) {
					Element sourceElement = e.getDocument().getDocumentElement();
					sourceElement.appendChild(e.toXml(e.getDocument()));
				}
				inv.sendOk(e.getDocument());
			} catch (UnauthorizedException e) {
				inv.sendUnauthorized();
			} catch (UserException e) {
				Document doc = e.getDocument();
				if (e.getMessage() != null) {
					Element sourceElement = doc.getDocumentElement();
					sourceElement.appendChild(e.toXml(doc));
				}
				inv.sendUser(doc);
			} catch (BadRequestException e) {
				inv.sendBadRequest(e.getMessage());
			}
		} catch (Throwable e) {
			try {
				new InternetAddress("tlocke@tlocke.org.uk");
			} catch (AddressException ae) {
			}
			logger.logp(Level.SEVERE, "uk.org.tlocke.monad.Monad", "service",
					"Can't process request", e);
			res
					.sendError(
							HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
							(e instanceof HttpException) ? e.getMessage()
									: "There has been an error with our software. The "
											+ "administrator has been informed, and the problem will "
											+ "be put right as soon as possible.");
		} finally {
			Hiber.rollBack();
			Hiber.close();
		}
	}

	static public void setConfigDir(File configDir) {
		Monad.CONFIG_DIR = configDir;
	}

	static public URL getConfigResource(MonadUri uri)
			throws HttpException {
		URL url = getConfigFile(uri);
		if (url == null) {
			url = getConfigUrl(uri);
		}
		return url;
	}

	static public URL getConfigFile(MonadUri uri) throws HttpException {
		URL url = null;
		try {
			MonadUri uriNew = getConfigFile(new MonadUri("/"), uri.toString()
					.substring(1).split("/"), 0);
			if (uriNew != null) {
				url = new File(CONFIG_DIR.toString() + File.separator
						+ uriNew.toString()).toURI().toURL();
			}
			return url;
		} catch (MalformedURLException e) {
			throw new InternalException(e);
		}
	}

	static public URL getConfigUrl(MonadUri uri) throws HttpException {
		URL url = null;
		try {
			MonadUri newUri = getConfigUrl(new MonadUri("/"), uri.toString()
					.substring(1).split("/"), 0);
			if (newUri != null) {
				url = Monad.getContext().getResource(
						CONFIG_PREFIX + newUri.toString());
			}
		} catch (MalformedURLException e) {
			throw new InternalException(e);
		}
		return url;
	}

	static public MonadUri getConfigUrl(MonadUri uri, String[] elements,
			int position) throws HttpException {
		List<String> urlElements = getConfigUrlElements(uri);
		MonadUri newUri = null;
		if (urlElements.contains(elements[position]
				+ (position == elements.length - 1 ? "" : "/"))) {
			newUri = uri.resolve(elements[position]);
			if (position < elements.length - 1) {
				newUri = newUri.append("/");
				newUri = getConfigUrl(newUri, elements, position + 1);
			}
		}
		if (newUri == null
				&& urlElements.contains("default"
						+ (position == elements.length - 1 ? "" : "/"))) {
			if (position < elements.length - 1) {
				newUri = uri.append("default/");
				newUri = getConfigUrl(newUri, elements, position + 1);
			}
		}
		return newUri;
	}

	static public MonadUri getConfigFile(MonadUri uri, String[] elements,
			int position) throws HttpException {
		List<String> fileElements = getConfigFileElements(uri);
		MonadUri newUri = null;
		if (fileElements.contains(elements[position])) {
			newUri = uri.resolve(elements[position]);
			if (position < elements.length - 1) {
				newUri = newUri.append("/");
				newUri = getConfigFile(newUri, elements, position + 1);
			}
		}
		if (newUri == null && fileElements.contains("default")) {
			newUri = uri.append("default/");
			if (position < elements.length - 1) {
				newUri = getConfigFile(newUri, elements, position + 1);
			}
		}
		return newUri;
	}

	@SuppressWarnings("unchecked")
	static public List<String> getConfigFileElements(MonadUri uri)
			throws InternalException {
		List<String> urlElements = new ArrayList<String>();
		if (Monad.getConfigDir() != null) {
			File urlsPath = new File(Monad.getConfigDir().toString()
					+ uri.toString().replace("/", File.separator));
			String[] files = urlsPath.list();
			if (files != null) {
				for (String file : files) {
					urlElements.add(file);
				}
			}
		}
		return urlElements;
	}

	@SuppressWarnings("unchecked")
	static public List<String> getConfigUrlElements(MonadUri uri) {
		List<String> urlElements = new ArrayList<String>();
		String resourcePath = Monad.getConfigPrefix() + uri.toString();
		Set<String> paths = Monad.getContext().getResourcePaths(resourcePath);
		if (paths != null) {
			for (String path : paths) {
				if (!urlElements.contains(path)) {
					urlElements.add(path.substring(resourcePath.length()));
				}
			}
		}
		return urlElements;
	}

	static public InputStream getConfigIs(String path, String name)
			throws HttpException {
		InputStream is = null;
		try {
			URL url = getConfigResource(new MonadUri(path).append(name));
			if (url != null) {
				is = url.openStream();
			}
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return is;
	}

	@SuppressWarnings("unchecked")
	static public void returnStream(Document doc, String templatePath,
			String templateName, Result result) throws HttpException {
		TransformerFactory tf = TransformerFactory.newInstance();
		InputStream templateIs = null;
		InputStream debugIs = null;
		Transformer transformer;
		tf.setURIResolver(new ElectedURIResolver());
		if (templatePath != null && templateName != null) {
			templateIs = getConfigIs(templatePath, templateName);
			if (templateIs == null) {
				throw new DesignerException("The resource '" + templatePath
						+ " : " + templateName
						+ "' is needed but does not exist.");
			}
			debugIs = getConfigIs(templatePath, DEBUG_FILE_NAME);
		}
		try {
			if (debugIs != null) {
				StringWriter sr = new StringWriter();

				transformer = tf.newTransformer();
				transformer.setOutputProperty(OutputKeys.INDENT, "yes");
				// transformer.setOutputProperty(
				// "{http://xml.apache.org/xslt}indent-amount", "2");
				transformer.transform(new DOMSource(doc), new StreamResult(sr));
				logger.logp(Level.INFO, "uk.org.tlocke.monad.Monad",
						"returnStream", sr.toString());
			}
			transformer = templateIs == null ? tf.newTransformer() : tf
					.newTransformer(new StreamSource(templateIs));
			transformer.setOutputProperty(OutputKeys.INDENT, "yes");
			transformer.transform(new DOMSource(doc), result);
		} catch (TransformerConfigurationException e) {
			Throwable throwable = e.getCause();
			throw new UserException("Problem transforming template '"
							+ templatePath
							+ " : "
							+ templateName
							+ " "
							+ e.getMessageAndLocation()
							+ e.getMessage()
							+ e.getLocationAsString()
							+ " "
							+ e.getLocator()
							+ (throwable == null ? "" : " Problem type : "
									+ throwable.getClass().getName()
									+ " Message: " + throwable.getMessage()));
		} catch (TransformerException e) {
			throw new UserException("Problem transforming template '"
							+ templatePath + " : " + templateName + "'. "
							+ e.getMessageAndLocation() + " "
							+ " Problem type : "
							+ e.getCause().getClass().getName() + " Message: "
							+ e.getException().getMessage() + "Stack trace: "
							+ MonadUtils.getStackTrace(e.getException()) + e);
		}
	}

	static private class ElectedURIResolver implements URIResolver {
		public Source resolve(String href, String base) {
			Source source = null;
			try {
				source = new StreamSource(getConfigIs(base, href));
			} catch (InternalException e) {
				throw new RuntimeException(e);
			} catch (DesignerException e) {
				throw new RuntimeException(e);
			} catch (HttpException e) {
				throw new RuntimeException(e);
			}
			return source;
		}
	}

	public static Urlable dereferenceUri(URI uri) throws HttpException,
			InternalException {
		Urlable urlable = urlableRoot;
		String pathInfo = uri.getPath();
		if (pathInfo.length() > 1) {
			pathInfo = pathInfo.substring(1);
		}
		for (String element : pathInfo.split("/")) {
			urlable = urlable.getChild(new UriPathElement(element));
			if (urlable == null) {
				break;
			}
		}
		return urlable;
	}

	public MonadUri getUri() throws InternalException {
		return URI;
	}
}