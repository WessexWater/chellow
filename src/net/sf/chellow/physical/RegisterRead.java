package net.sf.chellow.physical;

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class RegisterRead extends PersistentEntity {
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
	}

	public RegisterRead(Mpan mpan, RegisterReadRaw rawRegisterRead,
			Invoice invoice) throws HttpException, InternalException {
		this();
		setMpan(mpan);
		if (invoice == null) {
			throw new InternalException("The invoice must not be null.");
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

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			Document doc = document();
			Element source = doc.getDocumentElement();
			source.appendChild(new MonadMessage(
					"This register read has been successfully deleted.")
					.toXml(doc));
			inv.sendOk(doc);
		}
	}

	public void delete() {
		Hiber.session().delete(this);
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("invoice", new XmlTree("batch",
								new XmlTree("service", new XmlTree("provider", new XmlTree(
										"organization"))))).put(
								"mpan",
								new XmlTree("supplyGeneration", new XmlTree("supply"))
										.put("mpanRaw")).put("tpr")));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("register-read");
		Element element = (Element) super.toXml(doc);
		element.setAttribute("coefficient", Float.toString(coefficient));
		element.setAttribute("units", units.toString());
		element.setAttribute("is-import", Boolean.toString(isImport));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXml(doc));
		element.setAttribute("previous-value", Float.toString(previousValue));
		element.setAttribute("previous-type", previousType.toString());
		presentDate.setLabel("present");
		element.appendChild(presentDate.toXml(doc));
		element.setAttribute("present-value", Float.toString(presentValue));
		element.setAttribute("present-type", presentType.toString());
		return element;
	}
}
