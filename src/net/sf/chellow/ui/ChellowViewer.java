package net.sf.chellow.ui;


public class ChellowViewer  {
	/*
	public ChellowViewer() {
		super();
		setTemplateDirName("");
	}

	public void init(ServletConfig conf) throws ServletException {
		super.init(conf);
		ServletContext context = getServletContext();
		Properties mailProperties = new Properties();
		DesignerMethodFilter[] designerMethodFilters = {};

		setHibernateUtil(Hiber.getUtil());
		try {
			MonadContextParameters monadParameters = (MonadContextParameters) context
					.getAttribute("monadParameters");
			HostName mailHost = monadParameters.getMailHost();

			addDesignerMethod("defaultAction", designerMethodFilters);
			/*addDesignerMethod("siteSearchCode", designerMethodFilters);
			addDesignerMethod("showImport", designerMethodFilters);
			addDesignerMethod("importHeader", designerMethodFilters);*/
			// addDesignerMethod("siteSearchName", designerMethodFilters);
	/*
			if (mailHost != null) {
				mailProperties.setProperty("mail.host", mailHost.toString());
			}
		} catch (Throwable e) {
			logger.logp(Level.SEVERE, "net.sf.theelected.ui.Chellow", "init",
					"Can't initialize servlet.", e);
			throw new ServletException(e.getMessage());
		}
	}
*/
	/**
	 * returns information about the servlet
	 */
	/*
	public String getServletInfo() {
		return "Chellow electricity billing and reporting.";
	}

	public void defaultAction(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		if (inv.getRequest().getPathInfo().length() == 1) {
			returnPage(inv, MonadUtilsUI.newSourceDocument(), "home");
		} else {
		try {
			StaticServlet.process(inv.getRequest().getPathInfo(), getServletConfig().getServletContext(), inv.getRequest(), inv.getResponse());
			} catch (IOException e) {
				throw new ProgrammerException(e);
			}
		}
	}
	*/
}