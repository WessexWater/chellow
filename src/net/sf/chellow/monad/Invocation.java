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

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.InvocationTargetException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;

import javax.servlet.ServletContext;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.xml.transform.Result;
import javax.xml.transform.Source;
import javax.xml.transform.stream.StreamResult;

import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.GeoPoint;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadDouble;
import net.sf.chellow.monad.types.MonadFloat;
import net.sf.chellow.monad.types.MonadInteger;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.MonadValidatable;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.User;
import net.sf.chellow.ui.Chellow;

import org.apache.commons.fileupload.FileItem;
import org.apache.commons.fileupload.FileItemFactory;
import org.apache.commons.fileupload.FileUploadException;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.apache.commons.fileupload.servlet.ServletRequestContext;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.Base64;

public class Invocation {
	private HttpServletRequest req;

	private HttpServletResponse res;

	private String action = null;

	private List<String> params = new ArrayList<String>();

	private List<FileItem> multipartItems;

	private Monad monad;

	private Map<String, Object> responseHeaders = new HashMap<String, Object>();

	private int responseStatusCode;

	public enum HttpMethod {
		OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE
	};

	@SuppressWarnings("unchecked")
	public Invocation(HttpServletRequest req, HttpServletResponse res,
			Monad monad) throws InternalException {
		this.monad = monad;
		String pathInfo;
		int start = 1;
		int finish;

		if ((this.req = req) == null) {
			throw new IllegalArgumentException("The 'req' argument must "
					+ "not be null.");
		}
		if ((this.res = res) == null) {
			throw new IllegalArgumentException("The 'res' argument must "
					+ "not be null.");
		}
		pathInfo = monad.getTemplateDirName().length() == 0 ? req
				.getServletPath() : req.getPathInfo();
		if (pathInfo != null) {
			while (start < pathInfo.length()) {
				finish = pathInfo.indexOf("/", start);
				if (finish == -1) {
					finish = pathInfo.length();
				}
				params.add(pathInfo.substring(start, finish));
				start = finish + 1;
			}
		}
		if (params.size() > 0) {
			action = (String) params.get(0);
		}
		if (ServletFileUpload
				.isMultipartContent(new ServletRequestContext(req))) {
			FileItemFactory factory = new DiskFileItemFactory();
			ServletFileUpload upload = new ServletFileUpload(factory);
			try {
				multipartItems = upload.parseRequest(req);
			} catch (FileUploadException e) {
				throw new InternalException(e);
			}
		}
	}

	public String getAction() {
		return action;
	}

	public HttpServletRequest getRequest() {
		return req;
	}

	public HttpServletResponse getResponse() {
		return res;
	}

	public Monad getMonad() {
		return monad;
	}

	/*
	 * will implement when need site and case public File getTemplateDirectory()
	 * throws DeployerException, ProgrammerException { MonadProperties
	 * properties = MonadProperties.newInstance(); File sitesDirectory =
	 * properties.getSitesDirectory(); File templateDirectory = new
	 * File(properties.getSitesDirectory(), req.getServerName() + File.separator
	 * + "templates");
	 * 
	 * if (sitesDirectory == null) { sitesUrl =
	 * context.getResource("/WEB-INF/sites/"
	 * UtilsBO.checkDirectory(templateDirectory); return templateDirectory; }
	 */

	public String[] getParameterValues(ParameterName paramName) {
		String[] values = null;

		if (ServletFileUpload
				.isMultipartContent(new ServletRequestContext(req))) {
			List<String> valueList = new ArrayList<String>();
			for (FileItem item : multipartItems) {
				if (item.isFormField()
						&& item.getFieldName().equals(paramName.toString())) {
					valueList.add(item.getString());
				}
			}
			if (valueList.size() > 0) {
				values = new String[valueList.size()];
				for (int i = 0; i < valueList.size(); i++) {
					values[i] = (String) valueList.get(i);
				}
			}
		} else {
			values = req.getParameterValues(paramName.toString());

		}
		return values;
	}

	protected List<MonadInstantiationException> instantiationExceptions = new ArrayList<MonadInstantiationException>();

	public <T extends MonadValidatable> T getValidatable(Class<T> clazz,
			String parameterName) throws InternalException {
		return getValidatable(clazz, new String[] { parameterName },
				parameterName);
	}

	public <T extends MonadValidatable> T getValidatable(Class<T> clazz,
			String[] parameterNamesString, String label)
			throws InternalException {
		ParameterName[] parameterNames = null;

		if (parameterNamesString != null) {
			parameterNames = new ParameterName[parameterNamesString.length];
			for (int i = 0; i < parameterNamesString.length; i++) {
				parameterNames[i] = new ParameterName(parameterNamesString[i]);
			}
		}
		return getValidatable(clazz, parameterNames, null, label);
	}

	public Long getLong(String parameterName) throws InternalException {
		MonadLong monadLong = null;
		HttpParameter parameter = null;
		try {
			parameter = (HttpParameter) getParameters(
					new ParameterName[] { new ParameterName(parameterName) })
					.get(0);
			String parameterValue = parameter.getFirstValue();
			if (!parameterValue.equals("null")) {
				monadLong = new MonadLong(parameterValue);
			}
		} catch (HttpException e) {
			instantiationExceptions.add(new MonadInstantiationException(
					Long.class.getName(), parameterName, e));
		}
		return monadLong == null ? null : monadLong.getLong();
	}

	public boolean getBoolean(String parameterName) throws InternalException {
		if (hasParameter(parameterName)
				&& getString(parameterName).equals("true")) {
			return true;

		} else {
			return false;
		}
	}

	public Date getDate(String baseName) throws InternalException {
		MonadDate date = getMonadDate(baseName);
		if (date == null) {
			return null;
		} else {
			return date.getDate();
		}
	}

	public Date getDateTime(String baseName) throws HttpException {
		Integer year = getInteger(baseName + "-year");
		Integer month = getInteger(baseName + "-month");
		Integer day = getInteger(baseName + "-day");
		Integer hour = getInteger(baseName + "-hour");
		Integer minute = getInteger(baseName + "-minute");
		Date date = null;
		if (isValid()) {
			MonadDate mDate = new MonadDate(year, month, day, hour, minute);
			if (isValid()) {
				date = mDate.getDate();
			}
		}
		return date;
	}

	public MonadDate getMonadDate(String baseName) throws InternalException {
		return getValidatable(MonadDate.class, new String[] {
				baseName + "-year", baseName + "-month", baseName + "-day" },
				baseName);
	}

	public GeoPoint getGeoPoint(String baseName) throws InternalException {
		return getValidatable(GeoPoint.class, new String[] {
				baseName + "-latitude", baseName + "-longitude" }, baseName);
	}

	public Integer getInteger(String parameterNameString)
			throws InternalException {
		MonadInteger monadInteger = getValidatable(MonadInteger.class,
				parameterNameString);
		return monadInteger == null ? null : monadInteger.getInteger();
	}

	public Float getFloat(String parameterNameString) throws InternalException {
		MonadFloat monadFloat = getValidatable(MonadFloat.class,
				parameterNameString);
		return monadFloat == null ? null : monadFloat.getFloat();
	}

	public BigDecimal getBigDecimal(String paramName) throws InternalException {
		if (hasParameter(paramName)) {
			return new BigDecimal(getString(paramName));
		} else {
			return null;
		}
	}
	
	public BigInteger getBigInteger(String paramName) throws InternalException {
		if (hasParameter(paramName)) {
			return new BigInteger(getString(paramName));
		} else {
			return null;
		}
	}

	public Double getDouble(String parameterNameString)
			throws InternalException {
		MonadDouble monadDouble = getValidatable(MonadDouble.class,
				parameterNameString);
		return monadDouble == null ? null : monadDouble.getDouble();
	}

	public MonadLong getMonadLong(String parameterNameString)
			throws InternalException {
		return getValidatable(MonadLong.class, parameterNameString);
	}

	public MonadUri getMonadUri(String parameterNameString)
			throws InternalException {
		return getValidatable(MonadUri.class, parameterNameString);
	}

	public UriPathElement getUriPathElement(String parameterNameString)
			throws InternalException {
		return getValidatable(UriPathElement.class, parameterNameString);
	}

	public EmailAddress getEmailAddress(String parameterNameString)
			throws InternalException {
		return getValidatable(EmailAddress.class, parameterNameString);
	}

	public MonadInteger getMonadInteger(String parameterNameString)
			throws InternalException {
		return getValidatable(MonadInteger.class, parameterNameString);
	}

	public MonadDouble getMonadDouble(String parameterNameString)
			throws InternalException {
		return getValidatable(MonadDouble.class, parameterNameString);
	}

	public String getString(String parameterName) throws InternalException {
		MonadString monadString = getMonadString(parameterName);
		if (monadString != null) {
			return monadString.getString();
		} else {
			return null;
		}
	}

	public Character getCharacter(String parameterName)
			throws InternalException {
		MonadString monadString = getMonadString(parameterName);
		if (monadString != null) {
			String chars = monadString.getString();
			if (chars.length() > 0) {
				return chars.charAt(0);
			} else {
				return null;
			}
		} else {
			return null;
		}
	}

	public MonadString getMonadString(String parameterNameString)
			throws InternalException {
		return getValidatable(MonadString.class, parameterNameString);
	}

	public <T extends MonadValidatable> T getValidatable(Class<T> clazz,
			ParameterName[] parameterNames, List<? extends Object> list,
			String label) throws InternalException {
		T obj = null;
		List<HttpParameter> parameters = null;

		try {
			parameters = getParameters(parameterNames);
			Object[] parameterValues = new Object[parameters.size()
					+ ((list == null) ? 1 : 2)];
			Class<?>[] constructorClasses = new Class[parameters.size()
					+ ((list == null) ? 1 : 2)];
			parameterValues[0] = label;
			constructorClasses[0] = String.class;
			for (int i = 0; i < parameters.size(); i++) {
				parameterValues[i + 1] = ((HttpParameter) parameters.get(i))
						.getFirstValue();
				constructorClasses[i + 1] = String.class;
			}
			if (list != null) {
				constructorClasses[constructorClasses.length - 1] = List.class;
				parameterValues[parameterValues.length - 1] = list;
			}
			obj = clazz.getConstructor(constructorClasses).newInstance(
					parameterValues);
		} catch (IllegalArgumentException e) {
			throw new InternalException(e);
		} catch (InstantiationException e) {
			throw new InternalException(e);
		} catch (IllegalAccessException e) {
			throw new InternalException(e);
		} catch (InvocationTargetException e) {
			if (e.getCause() instanceof HttpException) {
				instantiationExceptions.add(new MonadInstantiationException(
						clazz.getName(), label, (HttpException) e.getCause()));
			} else {
				throw new InternalException(e);
			}
		} catch (SecurityException e) {
			throw new InternalException(e);
		} catch (NoSuchMethodException e) {
			throw new InternalException(e);
		} catch (InternalException e) {
			instantiationExceptions.add(new MonadInstantiationException(clazz
					.getName(), label, new UserException(e.getMessage())));
		} catch (HttpException e) {
			instantiationExceptions.add(new MonadInstantiationException(clazz
					.getName(), label, e));
		}
		return obj;
	}

	public final boolean isValid() {
		return instantiationExceptions.isEmpty();
	}

	public void setResponseStatusCode(int statusCode) {
		responseStatusCode = statusCode;
		res.setStatus(statusCode);
	}

	public Node responseXml(Document doc) throws InternalException {
		Element responseElement = doc.createElement("response");
		for (Map.Entry<String, Object> entry : responseHeaders.entrySet()) {
			Element headerElement = doc.createElement("header");
			headerElement.setAttribute("name", entry.getKey());
			headerElement.setAttribute("value", entry.getValue().toString());
			responseElement.appendChild(headerElement);
		}
		responseElement.setAttribute("status-code", Integer
				.toString(responseStatusCode));
		return responseElement;
	}

	public void setResponseHeader(String name, String value) {
		res.setHeader(name, value);
		responseHeaders.put(name, value);
	}

	@SuppressWarnings("unchecked")
	public Element requestXml(Document doc) throws HttpException {
		Element requestElement = doc.createElement("request");
		Map<String, String[]> parameterMap = getRequest().getParameterMap();

		requestElement.setAttribute("context-path", getRequest()
				.getContextPath());
		requestElement.setAttribute("path-info", getRequest().getPathInfo());
		requestElement.setAttribute("method", getRequest().getMethod()
				.toLowerCase());
		requestElement
				.setAttribute("server-name", getRequest().getServerName());
		for (Entry<String, String[]> entry : parameterMap.entrySet()) {
			requestElement.appendChild(new HttpParameter(new ParameterName(
					entry.getKey()), entry.getValue()).toXml(doc));
		}
		if (ServletFileUpload
				.isMultipartContent(new ServletRequestContext(req))) {
			for (Iterator it = multipartItems.iterator(); it.hasNext();) {
				FileItem item = (FileItem) it.next();
				requestElement.appendChild(new HttpParameter(new ParameterName(
						item.getFieldName()), item.isFormField() ? item
						.getString() : item.getName()).toXml(doc));
			}
		}
		for (MonadInstantiationException e : instantiationExceptions) {
			requestElement.appendChild(e.toXml(doc));
		}
		return requestElement;
	}

	public FileItem getFileItem(String name) throws InternalException {
		FileItem fileItem = null;

		for (FileItem item : multipartItems) {
			if (!item.isFormField() && item.getFieldName().equals(name)) {
				fileItem = item;
			}
		}
		if (fileItem == null) {
			instantiationExceptions.add(new MonadInstantiationException(
					FileItem.class.getName(), name, new UserException(
							"File parameter '" + name + "' is required.")));
		}
		return fileItem;
	}

	public List<HttpParameter> getParameters(ParameterName[] parameterNames)
			throws HttpException {
		List<HttpParameter> parameters = new ArrayList<HttpParameter>();
		if (parameterNames != null) {
			for (int i = 0; i < parameterNames.length; i++) {
				String[] parameterValues = getParameterValues(parameterNames[i]);

				if (parameterValues == null || parameterValues.length < 1) {
					throw new UserException("The parameter '"
							+ parameterNames[i] + "' is required.");
				} else if (parameterValues.length > 1) {
					throw new UserException("Too many parameter values.");
				}
				parameters.add(new HttpParameter(parameterNames[i],
						parameterValues[0]));
			}
		}
		return parameters;
	}

	public void sendCreated(MonadUri uri) throws HttpException {
		sendCreated(null, uri);
	}

	public void sendBadRequest(String message) throws HttpException {
		try {
			res.sendError(HttpServletResponse.SC_BAD_REQUEST, message);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public void sendFound(MonadString uri) throws HttpException {
		sendFound(uri.toString());
	}

	public void sendFound(String uri) throws HttpException {
		URI locationUri;
		try {
			locationUri = new URI(req.getScheme(), null, req.getServerName(),
					req.getServerPort(), req.getContextPath() + uri, null, null);
			setResponseHeader("Location", locationUri.toString());
			res.sendError(HttpServletResponse.SC_FOUND);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
	}

	public void sendCreated(Document doc, MonadUri uri) throws HttpException {
		URI locationUri;
		try {
			locationUri = new URI(req.getScheme(), null, req.getServerName(),
					req.getServerPort(), req.getContextPath() + uri.toString(),
					null, null);
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
		setResponseHeader("Location", locationUri.toString());
		setResponseStatusCode(HttpServletResponse.SC_CREATED);
		returnPage(doc, req.getPathInfo(), "template.xsl");
	}

	public void sendMovedPermanently(URI location) throws InternalException {
		res.setHeader("Location", location.toString());
		try {
			res.sendError(HttpServletResponse.SC_MOVED_PERMANENTLY);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public HttpMethod getMethod() throws HttpException {
		String method = req.getMethod();
		if (method.equals("GET")) {
			return HttpMethod.GET;
		} else if (method.equals("POST")) {
			return HttpMethod.POST;
		} else if (method.equals("DELETE")) {
			return HttpMethod.DELETE;
		} else {
			throw new NotImplementedException();
		}
	}

	public void sendUser(Document doc) throws HttpException {
		res.setStatus(418);
		returnPage(doc, req.getPathInfo(), "template.xsl");
	}

	public void sendOk() throws HttpException {
		sendOk(null);
	}

	public void sendOk(Document doc, String templatePath, String templateName)
			throws HttpException {
		res.setStatus(HttpServletResponse.SC_OK);
		returnPage(doc, templatePath, templateName);
	}

	public void sendOk(Document doc, Source templateSource)
			throws HttpException {
		res.setStatus(HttpServletResponse.SC_OK);
		returnPage(doc, templateSource);
	}

	public void sendOk(Document doc) throws HttpException {
		String templatePath = req.getPathInfo();
		if (templatePath == null) {
			templatePath = "/";
		}
		sendOk(doc, templatePath, "template.xsl");
	}

	public void sendForbidden(String message) throws InternalException {
		try {
			res.sendError(HttpServletResponse.SC_FORBIDDEN, message);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public void sendNotFound(String message) throws InternalException {
		try {
			res.sendError(HttpServletResponse.SC_NOT_FOUND, message);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public void sendNotFound(Document doc) throws HttpException {
		res.setStatus(HttpServletResponse.SC_NOT_FOUND);
		returnPage(doc, req.getPathInfo(), "template.xsl");
	}

	public void sendUnauthorized(String message) throws InternalException {
		res.setHeader("WWW-Authenticate", "Basic realm=\""
				+ monad.getRealmName() + "\"");
		try {
			res.sendError(HttpServletResponse.SC_UNAUTHORIZED, message);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public void sendMethodNotAllowed(HttpMethod[] methods)
			throws InternalException {
		try {
			StringBuilder methodsString = new StringBuilder();
			for (int i = 0; i < methodsString.length(); i++) {
				if (i != 0) {
					methodsString.append(", ");
				}
				methodsString.append(methods[i]);
			}
			res.setHeader("Allow", methodsString.toString());
			res.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public void sendSeeOther(MonadUri uri) throws InternalException {
		try {
			URI locationUri = new URI(req.getScheme(), null, req
					.getServerName(), req.getServerPort(), req.getContextPath()
					+ uri.toString(), null, null);
			res.setHeader("Location", locationUri.toString());
			res.sendError(HttpServletResponse.SC_SEE_OTHER);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
	}

	public User getUser() throws HttpException {
		String authHeader = req.getHeader("Authorization");
		if (authHeader == null || !authHeader.startsWith("Basic")) {
			return null;
		}
		String[] usernameAndPassword = Base64.decode(authHeader.substring(6))
				.split(":");
		if (usernameAndPassword == null || usernameAndPassword.length != 2) {
			return null;
			// throw new BadRequestException(
			// "The Authorization header must contain a base64 encoded string
			// consisting of a username and password separated by a ':'.");
		}
		User user = Chellow.USERS_INSTANCE.findUser(new EmailAddress(
				usernameAndPassword[0]));
		if (user == null) {
			return null;
		} else if (!user.getPasswordDigest().equals(
				User.digest(usernameAndPassword[1]))) {
			return null;
		}
		return user;
	}

	private void returnPage(Document doc, String templatePath,
			String templateName) throws HttpException {
		if (hasParameter("view") && getString("view").equals("xml")) {
			templatePath = null;
		}
		if (doc == null) {
			doc = MonadUtils.newSourceDocument();
		}
		Result result;
		Element source = doc.getDocumentElement();

		if (source == null) {
			throw new InternalException(
					"There is no child element for "
							+ " a document requiring the template 'template'. Request URL: "
							+ getRequest().getRequestURL().toString() + "?"
							+ getRequest().getQueryString());
		}
		source.appendChild(requestXml(doc));
		source.appendChild(responseXml(doc));
		if (templatePath == null) {
			res.setContentType("text/xml");
		} else {
			res.setContentType("text/html;charset=us-ascii");
		}
		res.setDateHeader("Date", System.currentTimeMillis());
		res.setHeader("Cache-Control", "no-cache");
		try {
			result = new StreamResult(getResponse().getWriter());
		} catch (IOException e) {
			throw new InternalException(e);
		}
		Monad.returnStream(doc, templatePath, templateName, result);
	}

	private void returnPage(Document doc, Source templateSource)
			throws HttpException {
		try {
			Element source = doc.getDocumentElement();
			source.appendChild(requestXml(doc));
			source.appendChild(responseXml(doc));
			getResponse().setContentType("text/html;charset=us-ascii");
			res.setDateHeader("Date", System.currentTimeMillis());
			res.setHeader("Cache-Control", "no-cache");
			Result result = new StreamResult(getResponse().getWriter());
			Monad.returnStream(doc, templateSource, result);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	/*
	 * private void returnStandardPage(Document doc, String templatePath, String
	 * templateName) throws DesignerException, ProgrammerException,
	 * DeployerException, UserException { if (doc == null) { doc =
	 * MonadUtilsUI.newSourceDocument(); } Result result; Element source =
	 * doc.getDocumentElement();
	 * 
	 * if (source == null) { throw new ProgrammerException( "There is no child
	 * element for " + " a document requiring the template 'template'. Request
	 * URL: " + getRequest().getRequestURL().toString() + "?" +
	 * getRequest().getQueryString()); } source.appendChild(requestXml(doc));
	 * source.appendChild(responseXml(doc));
	 * getResponse().setContentType("text/html;charset=us-ascii");
	 * res.setDateHeader("Date", System.currentTimeMillis());
	 * res.setHeader("Cache-Control", "no-cache"); try { result = new
	 * StreamResult(getResponse().getWriter()); } catch (IOException e) { throw
	 * new ProgrammerException(e); } Monad.returnStream(doc, templatePath,
	 * templateName, result); }
	 */
	/*
	 * private void returnSvgPage(Document doc, String templatePath, String
	 * templateName) throws DesignerException, ProgrammerException,
	 * DeployerException, UserException { if (doc == null) { doc =
	 * MonadUtilsUI.newSourceDocument(); }
	 * 
	 * Element source = doc.getDocumentElement();
	 * 
	 * if (source == null) { throw new ProgrammerException( "There is no child
	 * element for " + " a document requiring the template 'template'. Request
	 * URL: " + getRequest().getRequestURL().toString() + "?" +
	 * getRequest().getQueryString()); } // source.appendChild(requestXml(doc));
	 * // source.appendChild(responseXml(doc)); //
	 * getResponse().setContentType("text/html;charset=us-ascii");
	 * res.setContentType("image/png"); res.setDateHeader("Date",
	 * System.currentTimeMillis()); res.setHeader("Cache-Control", "no-cache");
	 * StringWriter stringWriter = new StringWriter(); Monad.returnStream(doc,
	 * templatePath, templateName, new StreamResult( stringWriter));
	 * PNGTranscoder t = new PNGTranscoder(); TranscoderInput input = new
	 * TranscoderInput(new StringReader( stringWriter.toString()));
	 * TranscoderOutput output; try { output = new
	 * TranscoderOutput(getResponse().getOutputStream()); t.transcode(input,
	 * output); } catch (IOException e) { throw new ProgrammerException(e); }
	 * catch (TranscoderException e) { throw new ProgrammerException(e); } }
	 */
	public boolean hasParameter(String parameterName) {
		boolean found = req.getParameter(parameterName) != null;
		if (!found && multipartItems != null) {
			for (FileItem item : multipartItems) {
				if (!item.isFormField()
						&& item.getFieldName().equals(parameterName)) {
					found = true;
					break;
				}
			}
		}
		return found;
	}

	@SuppressWarnings("unchecked")
	public void returnStatic(ServletContext servletContext, String uri)
			throws HttpException, InternalException {
		InputStream is;
		try {
			res.setDateHeader("Expires", System.currentTimeMillis() + 24 * 60
					* 60 * 1000);
			OutputStream os = res.getOutputStream();
			if (uri == null) {
				throw new NotFoundException();
			}
			if (uri.endsWith("/")) {
				uri = uri.substring(0, uri.length() - 1);
			}
			int lastSlash = uri.lastIndexOf("/");
			String resourcePath = uri.substring(0, lastSlash + 1);
			URL url;
			Set<String> paths = servletContext.getResourcePaths(resourcePath);
			if (paths == null) {
				throw new NotFoundException();
			}
			String potentialPath = null;
			for (String candidatePath : paths) {
				if (!candidatePath.endsWith("/")
						&& candidatePath.startsWith(uri + ".")) {
					potentialPath = candidatePath;
					break;
				}
			}
			if (potentialPath == null) {
				throw new NotFoundException();
			}
			url = servletContext.getResource(potentialPath);
			if (url == null) {
				throw new NotFoundException();
			}
			URLConnection con = url.openConnection();
			String contentType = servletContext.getMimeType(url.toString());
			int c;

			con.connect();
			is = con.getInputStream();
			if (contentType != null) {
				res.setContentType(contentType);
			}
			while ((c = is.read()) != -1) {
				os.write(c);
			}
			os.close();
			is.close();
		} catch (MalformedURLException e) {
			throw new BadRequestException();
		} catch (FileNotFoundException e) {
			throw new NotFoundException();
		} catch (IOException e) {
		}
	}

	public Urlable dereferenceUrl() throws HttpException, InternalException {
		try {
			String pathInfo = req.getPathInfo();
			return Monad.dereferenceUri(new URI(pathInfo == null ? "/"
					: pathInfo));
		} catch (URISyntaxException e1) {
			throw new BadRequestException();
		}
	}

	private class MonadInstantiationException extends Exception implements
			XmlDescriber {
		private static final long serialVersionUID = 1L;

		private MonadMessage message = null;

		private String typeName;

		private String label;

		public MonadInstantiationException(String typeName, String label,
				HttpException e) {
			this(typeName, label, e.getMessage());
		}

		public MonadInstantiationException(String typeName, String label,
				MonadMessage message) {
			this(typeName, label);
			this.message = message;
		}

		public MonadInstantiationException(String typeName, String label) {
			this.typeName = typeName;
			this.label = label;
		}

		public MonadInstantiationException(String typeName, String label,
				String messageCode) {
			this(typeName, label, new MonadMessage(messageCode));
		}

		public String getMessage() {
			return message.getDescription();
		}

		public Node toXml(Document doc) throws HttpException {
			Element element = doc.createElement(typeName);

			if (label != null) {
				element.setAttribute("label", label);
			}

			if (message != null) {
				element.appendChild(message.toXml(doc));
			}
			return element;
		}

		public Node toXml(Document doc, XmlTree tree) throws HttpException {
			return toXml(doc);
		}
	}
}
