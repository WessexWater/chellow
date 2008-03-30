package net.sf.chellow.physical;

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class RegisterRead extends PersistentEntity {
	public static final int TYPE_NORMAL = 0;

	public static final int TYPE_MANUAL_ESTIMATE = 1;

	public static final int TYPE_COMPUTER_ESTIMATE = 2;

	public static final int TYPE_REMOVED = 3;

	public static final int TYPE_CUSTOMER = 4;

	public static final int TYPE_COMPUTER = 5;

	public static final int TYPE_EXCHANGE = 6;

	private Mpan mpan;

	private Invoice invoice;

	private float coefficient;

	private Units units;

	private Tpr tpr;

	private boolean isImport;

	private DayFinishDate previousDate;

	private float previousValue;

	private ReadType previousType;

	private DayFinishDate presentDate;

	private float presentValue;

	private ReadType presentType;

	RegisterRead() {
		setTypeName("register-read");
	}

	public RegisterRead(Mpan mpan, RegisterReadRaw rawRegisterRead,
			Invoice invoice) throws UserException, ProgrammerException {
		this();
		setMpan(mpan);
		if (invoice == null) {
			throw new ProgrammerException("The invoice must not be null.");
		}
		setInvoice(invoice);
		setTpr(Tpr.getTpr(rawRegisterRead.getTpr()));
		setCoefficient(rawRegisterRead.getCoefficient());
		setUnits(rawRegisterRead.getUnits());
		setIsImport(rawRegisterRead.getIsImport());
		setPreviousDate(rawRegisterRead.getPreviousDate());
		setPreviousValue(rawRegisterRead.getPreviousValue());
		setPreviousType(rawRegisterRead.getPreviousType());
		setPresentDate(rawRegisterRead.getPresentDate());
		setpresentValue(rawRegisterRead.getPresentValue());
		setpresentType(rawRegisterRead.getPresentType());

	}

	public Mpan getMpan() {
		return mpan;
	}

	void setMpan(Mpan mpan) {
		this.mpan = mpan;
	}

	public Invoice getInvoice() {
		return invoice;
	}

	void setInvoice(Invoice invoice) {
		this.invoice = invoice;
	}

	float getCoefficient() {
		return coefficient;
	}

	void setCoefficient(float coefficient) {
		this.coefficient = coefficient;
	}

	Units getUnits() {
		return units;
	}

	void setUnits(Units units) {
		this.units = units;
	}

	boolean getIsImport() {
		return isImport;
	}

	void setIsImport(boolean isImport) {
		this.isImport = isImport;
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	DayFinishDate getPreviousDate() {
		return previousDate;
	}

	void setPreviousDate(DayFinishDate previousDate) {
		this.previousDate = previousDate;
	}

	float getPreviousValue() {
		return previousValue;
	}

	void setPreviousValue(float previousValue) {
		this.previousValue = previousValue;
	}

	public ReadType getPreviousType() {
		return previousType;
	}

	void setPreviousType(ReadType previousType) {
		this.previousType = previousType;
	}

	public DayFinishDate getPresentDate() {
		return presentDate;
	}

	void setPresentDate(DayFinishDate presentDate) {
		this.presentDate = presentDate;
	}

	public float getpresentValue() {
		return presentValue;
	}

	void setpresentValue(float presentValue) {
		this.presentValue = presentValue;
	}

	public ReadType getpresentType() {
		return presentType;
	}

	void setpresentType(ReadType presentType) {
		this.presentType = presentType;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void delete() {
		Hiber.session().delete(this);
	}

	@SuppressWarnings("unchecked")
	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree("invoice", new XmlTree("batch",
				new XmlTree("service", new XmlTree("provider", new XmlTree(
						"organization"))))).put(
				"mpan",
				new XmlTree("supplyGeneration", new XmlTree("supply"))
						.put("mpanRaw")).put("tpr"), doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		element.setAttribute("coefficient", Float.toString(coefficient));
		element.setAttribute("units", units.toString());
		element.setAttribute("is-import", Boolean.toString(isImport));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXML(doc));
		element.setAttribute("previous-value", Float.toString(previousValue));
		element.setAttribute("previous-type", previousType.toString());
		presentDate.setLabel("present");
		element.appendChild(presentDate.toXML(doc));
		element.setAttribute("present-value", Float.toString(presentValue));
		element.setAttribute("present-type", presentType.toString());
		return element;
	}
}
