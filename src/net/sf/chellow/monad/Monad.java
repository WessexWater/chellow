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

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
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
import javax.xml.transform.stream.StreamSource;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Monad extends HttpServlet implements Urlable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

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

	static private final String CONFIG_PREFIX = "/WEB-INF/templates";

	protected Class<Invocation> invocationClass;

	static private ServletContext context;

	static private File CONFIG_DIR = null;

	private String templateDirName;

	static protected Logger logger = Logger
			.getLogger("uk.org.tlocke.theelected");

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
		// ARG_TYPES[0] = invocationClass;
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
	}

	protected abstract void checkPermissions(Invocation inv)
			throws HttpException;

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
						throw new MovedPermanentlyException(new URI(contextPath
								+ req.getPathInfo() + "/"));
					} catch (URISyntaxException e) {
						throw new BadRequestException(e.getMessage());
					}
				}
				try {
					checkPermissions(inv);
				} catch (UserException e) {
					throw new UnauthorizedException(e.getMessage());
				}
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
				inv.sendForbidden(e.getMessage());
			} catch (MovedPermanentlyException e) {
				inv.sendMovedPermanently(e.getLocation());
			} catch (NotFoundException e) {
				String message = e.getMessage();
				if (message == null) {
					message = e.getStackTraceString();
				}
				Document doc = e.getDocument();
				if (doc == null) {
					inv.sendNotFound(message);
				} else {
					Element sourceElement = doc.getDocumentElement();
					sourceElement.appendChild(e.toXml(doc));
					inv.sendNotFound(doc);
				}
			} catch (OkException e) {
				if (e.getMessage() != null) {
					Element sourceElement = e.getDocument()
							.getDocumentElement();
					sourceElement.appendChild(e.toXml(e.getDocument()));
				}
				inv.sendOk(e.getDocument());
			} catch (UnauthorizedException e) {
				inv.sendUnauthorized(e.getMessage());
			} catch (UserException e) {
				try {
					Document doc = e.getDocument();
					if (doc == null) {
						doc = MonadUtils.newSourceDocument();
					}
					if (e.getMessage() != null) {
						Element sourceElement = doc.getDocumentElement();
						sourceElement.appendChild(e.toXml(doc));
					}
					inv.sendUser(doc);
				} catch (Throwable te) {
					logger.logp(Level.SEVERE, "uk.org.tlocke.monad.Monad",
							"service", "Can't process request", e);
					res.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
							HttpException.getStackTraceString(te)
									+ HttpException.getStackTraceString(e));
				}
			} catch (BadRequestException e) {
				inv.sendBadRequest(e.getMessage());
			}
		} catch (Throwable e) {
			logger.logp(Level.SEVERE, "uk.org.tlocke.monad.Monad", "service",
					"Can't process request", e);
			logger.logp(Level.SEVERE, "uk.org.tlocke.monad.Monad", "service",
					"Can't process request", e);
			res.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
					HttpException.getStackTraceString(e));
		} finally {
			Hiber.rollBack();
			Hiber.close();
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
			URL url = getConfigUrl(new MonadUri(path).append(name));
			if (url != null) {
				is = url.openStream();
			}
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return is;
	}

	static public void returnStream(Document doc, String templatePath,
			String templateName, Result result) throws HttpException {
		if (templatePath != null && templateName != null) {
			InputStream templateIs = getConfigIs(templatePath, templateName);
			if (templateIs == null) {
				throw new DesignerException("The resource '" + templatePath
						+ " : " + templateName
						+ "' is needed but does not exist.");
			}
			returnStream(doc, new StreamSource(templateIs), result);
		} else {
			returnStream(doc, null, result);
		}
	}

	static public void returnStream(Document doc, Source templateSource,
			Result result) throws HttpException {
		try {
			TransformerFactory tf = TransformerFactory.newInstance();
			Transformer transformer = templateSource == null ? tf
					.newTransformer() : tf.newTransformer(templateSource);
			tf.setURIResolver(new ElectedURIResolver());
			transformer.setOutputProperty(OutputKeys.INDENT, "yes");
			transformer.transform(new DOMSource(doc), result);
		} catch (TransformerConfigurationException e) {
			Throwable throwable = e.getCause();
			throw new UserException("Transformer configuration problem: "
					+ e.getMessageAndLocation()
					+ (throwable == null ? "" : " Problem type : "
							+ throwable.getClass().getName() + " Message: "
							+ throwable.getMessage()));
		} catch (TransformerException e) {
			throw new UserException(
					"Problem transforming template, TransformerException '"
							+ " : "
							+ "'. "
							+ e.getMessageAndLocation()
							+ " "
							+ " Problem type : "
							+ e.getCause().getClass().getName()
							+ " Message: "
							+ e.getException().getMessage()
							+ "Stack trace: "
							+ HttpException.getStackTraceString(e
									.getException()) + e);
		}
	}

	/*
	 * @SuppressWarnings("unchecked") static public void returnStream(Document
	 * doc, String templatePath, String templateName, Result result) throws
	 * HttpException { TransformerFactory tf = TransformerFactory.newInstance();
	 * InputStream templateIs = null; InputStream debugIs = null; Transformer
	 * transformer; tf.setURIResolver(new ElectedURIResolver()); if
	 * (templatePath != null && templateName != null) { templateIs =
	 * getConfigIs(templatePath, templateName); if (templateIs == null) { throw
	 * new DesignerException("The resource '" + templatePath + " : " +
	 * templateName + "' is needed but does not exist."); } debugIs =
	 * getConfigIs(templatePath, DEBUG_FILE_NAME); } try { if (debugIs != null) {
	 * StringWriter sr = new StringWriter();
	 * 
	 * transformer = tf.newTransformer();
	 * transformer.setOutputProperty(OutputKeys.INDENT, "yes"); //
	 * transformer.setOutputProperty( //
	 * "{http://xml.apache.org/xslt}indent-amount", "2");
	 * transformer.transform(new DOMSource(doc), new StreamResult(sr));
	 * logger.logp(Level.INFO, "uk.org.tlocke.monad.Monad", "returnStream",
	 * sr.toString()); } transformer = templateIs == null ? tf.newTransformer() :
	 * tf .newTransformer(new StreamSource(templateIs));
	 * transformer.setOutputProperty(OutputKeys.INDENT, "yes");
	 * transformer.transform(new DOMSource(doc), result); } catch
	 * (TransformerConfigurationException e) { Throwable throwable =
	 * e.getCause(); throw new UserException("Problem transforming template '" +
	 * templatePath + " : " + templateName + " " + e.getMessageAndLocation() +
	 * e.getMessage() + e.getLocationAsString() + " " + e.getLocator() +
	 * (throwable == null ? "" : " Problem type : " +
	 * throwable.getClass().getName() + " Message: " + throwable.getMessage())); }
	 * catch (TransformerException e) { throw new UserException("Problem
	 * transforming template '" + templatePath + " : " + templateName + "'. " +
	 * e.getMessageAndLocation() + " " + " Problem type : " +
	 * e.getCause().getClass().getName() + " Message: " +
	 * e.getException().getMessage() + "Stack trace: " +
	 * HttpException.getStackTraceString(e.getException()) + e); } }
	 */
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

	public static Urlable dereferenceUri(URI uri) throws HttpException {
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
