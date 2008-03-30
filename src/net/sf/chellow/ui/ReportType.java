package net.sf.chellow.ui;

import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlDescriber;

public interface ReportType extends Urlable, XmlDescriber {
public Report getReport();
}
