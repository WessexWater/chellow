/*******************************************************************************
 * 
 *  Copyright (c) 2005 - 2013 Wessex Water Services Limited
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

package net.sf.chellow.physical;

public class Channel extends PersistentEntity {

	private Era era;

	private boolean isImport;

	private boolean isKwh;

	public Channel() {
	}

	public Channel(Era era, boolean isImport, boolean isKwh) {
		this.era = era;
		this.isImport = isImport;
		this.isKwh = isKwh;
	}

	public Era getEra() {
		return era;
	}

	void setEra(Era era) {
		this.era = era;
	}

	public boolean getIsImport() {
		return isImport;
	}

	void setIsImport(boolean isImport) {
		this.isImport = isImport;
	}

	public boolean getIsKwh() {
		return isKwh;
	}

	void setIsKwh(boolean isKwh) {
		this.isKwh = isKwh;
	}

	/*
	 * 
	 * public void siteCheck(HhStartDate from, HhStartDate to) throws
	 * HttpException { if (isKwh) { Site site =
	 * supplyGeneration.getSiteSupplyGenerations().iterator() .next().getSite();
	 * HhStartDate checkFrom = from.getDate().after(
	 * supplyGeneration.getStartDate().getDate()) ? from :
	 * supplyGeneration.getStartDate(); HhStartDate checkTo =
	 * supplyGeneration.getFinishDate() == null || to.getDate().before(
	 * supplyGeneration.getFinishDate().getDate()) ? to :
	 * supplyGeneration.getFinishDate(); site.hhCheck(checkFrom, checkTo); } }
	 * 
	 * public ChannelSnags snagsInstance() { return new ChannelSnags(this); }
	 * 
	 * public void addSnag(String description, HhStartDate startDate,
	 * HhStartDate finishDate) throws HttpException { SnagDateBounded
	 * .addChannelSnag(this, description, startDate, finishDate); }
	 * 
	 * void deleteSnag(String description, HhStartDate startDate, HhStartDate
	 * finishDate) throws HttpException {
	 * SnagDateBounded.deleteChannelSnag(this, description, startDate,
	 * finishDate); }
	 * 
	 * public void deleteSnag(String description, HhStartDate date) throws
	 * HttpException { deleteSnag(description, date, date); }
	 * 
	 * public void deleteData(HhStartDate from, HhStartDate to) throws
	 * HttpException { long numDeleted = Hiber .session() .createQuery(
	 * "delete from HhDatum datum where datum.channel = :channel and datum.startDate.date >= :from and datum.startDate.date <= :to"
	 * ) .setEntity("channel", this) .setTimestamp("from", from.getDate())
	 * .setTimestamp("to", to.getDate()).executeUpdate(); if (numDeleted == 0) {
	 * throw new UserException(
	 * "There aren't any data to delete for this period."); }
	 * addSnag(ChannelSnag.SNAG_MISSING, from, to); siteCheck(from, to); }
	 * 
	 * public Element toXml(Document doc) throws HttpException { Element element
	 * = super.toXml(doc, "channel"); element.setAttribute("is-import",
	 * Boolean.toString(isImport)); element.setAttribute("is-kwh",
	 * Boolean.toString(isKwh)); return element; }
	 * 
	 * private Document document() throws HttpException { Document doc =
	 * MonadUtils.newSourceDocument(); Element source =
	 * doc.getDocumentElement(); source.appendChild(toXml(doc, new
	 * XmlTree("supplyGeneration", new XmlTree("supply")))); return doc; }
	 * 
	 * public void httpGet(Invocation inv) throws HttpException {
	 * inv.sendOk(document()); }
	 * 
	 * public void httpPost(Invocation inv) throws HttpException {
	 * Hiber.setReadWrite(); try { if (inv.hasParameter("delete")) {
	 * supplyGeneration.deleteChannel(isImport, isKwh); Hiber.commit();
	 * inv.sendSeeOther(supplyGeneration.getChannelsInstance() .getEditUri()); }
	 * } catch (HttpException e) { e.setDocument(document()); throw e; } }
	 * 
	 * public HhData getHhDataInstance() { return new HhData(this); }
	 * 
	 * public Urlable getChild(UriPathElement uriId) throws HttpException { if
	 * (HhData.URI_ID.equals(uriId)) { return new HhData(this); } else if
	 * (ChannelSnags.URI_ID.equals(uriId)) { return snagsInstance(); } else {
	 * return null; } }
	 * 
	 * public MonadUri getEditUri() throws HttpException { return
	 * supplyGeneration.getChannelsInstance().getEditUri()
	 * .resolve(getUriId()).append("/"); }
	 * 
	 * public String toString() { return "Channel id: " + getId() +
	 * "is import: " + getIsImport() + " is kWh: " + getIsKwh(); }
	 * 
	 * @SuppressWarnings({ "unchecked", "deprecation" }) public void
	 * addHhData(List<HhDatumRaw> dataRaw) throws HttpException { // long now =
	 * System.currentTimeMillis(); HhDatumRaw firstRawDatum = dataRaw.get(0);
	 * HhDatumRaw lastRawDatum = dataRaw.get(dataRaw.size() - 1); //
	 * Debug.print("First dr = " + firstRawDatum + " cond dr " + //
	 * lastRawDatum); List<HhDatum> data = (List<HhDatum>) Hiber .session()
	 * .createQuery( "from HhDatum datum where datum.channel = :channel and " +
	 * "datum.startDate.date >= :startDate and datum.startDate.date <= :finishDate order by datum.startDate.date"
	 * ) .setEntity("channel", this) .setTimestamp("startDate",
	 * firstRawDatum.getStartDate().getDate()) .setTimestamp("finishDate",
	 * lastRawDatum.getStartDate().getDate()).list(); HhStartDate siteCheckFrom
	 * = null; HhStartDate siteCheckTo = null; HhStartDate notActualFrom = null;
	 * HhStartDate notActualTo = null; HhStartDate deleteMissingFrom = null;
	 * HhStartDate deleteMissingTo = null; HhStartDate lastAdditionDate = null;
	 * HhStartDate prevStartDate = null; int missing = 0; BigDecimal
	 * originalDatumValue = new BigDecimal(0); char originalDatumStatus =
	 * Character.UNASSIGNED; Connection con = Hiber.session().connection();
	 * PreparedStatement stmt; try { stmt = con .prepareStatement(
	 * "INSERT INTO hh_datum VALUES (nextval('hh_datum_id_sequence'), ?, ?, ?, ?)"
	 * ); } catch (SQLException e1) { throw new InternalException(e1); } int
	 * batchSize = 0; for (int i = 0; i < dataRaw.size(); i++) { //
	 * Debug.print("Start processing hh: " + (System.currentTimeMillis() // -
	 * now)); boolean added = false; boolean altered = false; HhDatumRaw
	 * datumRaw = dataRaw.get(i); HhDatum datum = null;
	 * 
	 * if (i - missing < data.size()) { datum = data.get(i - missing); if
	 * (!datumRaw.getStartDate().equals(datum.getStartDate())) { datum = null; }
	 * } if (datum == null) { // Debug.print("About to save datum: " // +
	 * (System.currentTimeMillis() - now)); try { stmt.setLong(1, getId());
	 * 
	 * stmt.setTimestamp(2, new Timestamp(datumRaw.getStartDate()
	 * .getDate().getTime())); stmt.setBigDecimal(3, datumRaw.getValue());
	 * stmt.setString(4, Character.toString(datumRaw.getStatus()));
	 * stmt.addBatch(); batchSize++; } catch (SQLException e) { throw new
	 * InternalException(e); } // Debug.print("Saved datum: " // +
	 * (System.currentTimeMillis() - now)); // Hiber.flush(); lastAdditionDate =
	 * datumRaw.getStartDate(); added = true; missing++; if (deleteMissingFrom
	 * == null) { deleteMissingFrom = datumRaw.getStartDate(); } deleteMissingTo
	 * = datumRaw.getStartDate(); // Debug.print("Resolved missing: " // +
	 * (System.currentTimeMillis() - now)); } else if
	 * (datumRaw.getValue().doubleValue() != datum.getValue() .doubleValue() ||
	 * datumRaw.getStatus() != datum.getStatus()) { //
	 * Debug.print("About to update datum: " + datum + " with " + // datumRaw +
	 * " " // + (System.currentTimeMillis() - now)); originalDatumValue =
	 * datum.getValue(); originalDatumStatus = datum.getStatus();
	 * datum.update(datumRaw.getValue(), datumRaw.getStatus()); Hiber.flush();
	 * altered = true; } // Debug.print("About to see if changed: " // +
	 * (System.currentTimeMillis() - now)); if (added || altered) { if
	 * (siteCheckFrom == null) { siteCheckFrom = datumRaw.getStartDate(); }
	 * siteCheckTo = datumRaw.getStartDate(); if
	 * (datumRaw.getValue().doubleValue() < 0) {
	 * addSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw.getStartDate(),
	 * datumRaw.getStartDate()); } else if (altered &&
	 * originalDatumValue.doubleValue() < 0) {
	 * deleteSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw.getStartDate()); } if
	 * (HhDatum.ACTUAL != datumRaw.getStatus()) { if (notActualFrom == null) {
	 * notActualFrom = datumRaw.getStartDate(); } notActualTo =
	 * datumRaw.getStartDate(); } else if (altered && originalDatumStatus !=
	 * HhDatum.ACTUAL) { deleteSnag(ChannelSnag.SNAG_ESTIMATED,
	 * datumRaw.getStartDate()); } } if (lastAdditionDate != null &&
	 * (lastAdditionDate.equals(prevStartDate) || batchSize > 100)) { //
	 * Debug.print("About to execute batch " // + (System.currentTimeMillis() -
	 * now)); try { stmt.executeBatch(); // Debug.print("Added  lines.");
	 * batchSize = 0; } catch (SQLException e) { throw new InternalException(e);
	 * } lastAdditionDate = null; } if (siteCheckTo != null &&
	 * siteCheckTo.equals(prevStartDate)) { //
	 * Debug.print("About to do site check: " // + (System.currentTimeMillis() -
	 * now)); siteCheck(siteCheckFrom, siteCheckTo); siteCheckFrom = null;
	 * siteCheckTo = null; // Debug.print("Finished site check: " // +
	 * (System.currentTimeMillis() - now)); } if (notActualTo != null &&
	 * notActualTo.equals(prevStartDate)) { //
	 * Debug.print("Started not actual: " // + (System.currentTimeMillis() -
	 * now)); addSnag(ChannelSnag.SNAG_ESTIMATED, notActualFrom, notActualTo);
	 * // Debug.print("Finished not actual: " // + (System.currentTimeMillis() -
	 * now)); notActualFrom = null; notActualTo = null; } if (deleteMissingTo !=
	 * null && deleteMissingTo.equals(prevStartDate)) { //
	 * Debug.print("Starting resolvedMissing: " // + (System.currentTimeMillis()
	 * - now)); deleteSnag(ChannelSnag.SNAG_MISSING, deleteMissingFrom,
	 * deleteMissingTo); deleteMissingFrom = null; deleteMissingTo = null; //
	 * Debug.print("Finished resolveMissing: " // + (System.currentTimeMillis()
	 * - now)); } prevStartDate = datumRaw.getStartDate(); } if
	 * (lastAdditionDate != null && lastAdditionDate.equals(prevStartDate)) { //
	 * Debug.print("About to execute batch 2: " // + (System.currentTimeMillis()
	 * - now)); try { stmt.executeBatch(); } catch (SQLException e) { throw new
	 * InternalException(e); } lastAdditionDate = null; } if (siteCheckTo !=
	 * null && siteCheckTo.equals(prevStartDate)) { //
	 * Debug.print("About to start site thing 2: " // +
	 * (System.currentTimeMillis() - now)); siteCheck(siteCheckFrom,
	 * siteCheckTo); // Debug.print("About to finish site thing 2: " // +
	 * (System.currentTimeMillis() - now)); } if (notActualTo != null &&
	 * notActualTo.equals(prevStartDate)) { //
	 * Debug.print("About to start not actual 2: " // +
	 * (System.currentTimeMillis() - now)); addSnag(ChannelSnag.SNAG_ESTIMATED,
	 * notActualFrom, notActualTo); //
	 * Debug.print("About to finsih not actual 2: " // +
	 * (System.currentTimeMillis() - now)); } if (deleteMissingTo != null &&
	 * deleteMissingTo.equals(prevStartDate)) { //
	 * Debug.print("About to start resolvem 2: " // +
	 * (System.currentTimeMillis() - now)); deleteSnag(ChannelSnag.SNAG_MISSING,
	 * deleteMissingFrom, deleteMissingTo); //
	 * Debug.print("About to finish resolvem 2: " // +
	 * (System.currentTimeMillis() - now)); } //
	 * Debug.print("Finished method 2: " + (System.currentTimeMillis() - //
	 * now)); }
	 * 
	 * @SuppressWarnings("unchecked") public void onSupplyGenerationChange()
	 * throws HttpException { List<ChannelSnag> snags = (List<ChannelSnag>)
	 * Hiber .session() .createQuery(
	 * "from ChannelSnag snag where snag.channel = :channel and snag.startDate.date < snag.channel.supplyGeneration.startDate.date order by snag.startDate.date"
	 * ) .setEntity("channel", this).list(); if (!snags.isEmpty()) { HhStartDate
	 * startDate = snags.get(0).getStartDate(); HhStartDate finishDate =
	 * supplyGeneration.getStartDate() .getPrevious();
	 * deleteSnag(ChannelSnag.SNAG_MISSING, startDate, finishDate);
	 * deleteSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate, finishDate);
	 * deleteSnag(ChannelSnag.SNAG_NEGATIVE, startDate, finishDate);
	 * deleteSnag(ChannelSnag.SNAG_ESTIMATED, startDate, finishDate); } if
	 * (supplyGeneration.getFinishDate() != null) { HhStartDate startDate =
	 * supplyGeneration.getFinishDate().getNext();
	 * deleteSnag(ChannelSnag.SNAG_MISSING, startDate, null);
	 * deleteSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate, null);
	 * deleteSnag(ChannelSnag.SNAG_NEGATIVE, startDate, null);
	 * deleteSnag(ChannelSnag.SNAG_ESTIMATED, startDate, null); }
	 * 
	 * // find date of first datum HhDatum firstDatum = (HhDatum) Hiber
	 * .session() .createQuery(
	 * "from HhDatum datum where datum.channel = :channel order by datum.startDate.date"
	 * ) .setEntity("channel", this).setMaxResults(1).uniqueResult(); if
	 * (firstDatum == null) { addSnag(ChannelSnag.SNAG_MISSING,
	 * supplyGeneration.getStartDate(), supplyGeneration.getFinishDate()); }
	 * else { if (firstDatum.getStartDate().getDate()
	 * .after(supplyGeneration.getStartDate().getDate())) {
	 * addSnag(ChannelSnag.SNAG_MISSING, supplyGeneration.getStartDate(),
	 * firstDatum .getStartDate().getPrevious()); } HhDatum lastDatum =
	 * (HhDatum) Hiber .session() .createQuery(
	 * "from HhDatum datum where datum.channel = :channel order by datum.startDate.date desc"
	 * ) .setEntity("channel", this).setMaxResults(1).uniqueResult(); if
	 * (supplyGeneration.getFinishDate() == null ||
	 * lastDatum.getStartDate().getDate()
	 * .before(supplyGeneration.getFinishDate().getDate())) {
	 * addSnag(ChannelSnag.SNAG_MISSING, lastDatum.getStartDate() .getNext(),
	 * supplyGeneration.getFinishDate()); } } }
	 * 
	 * @Override public URI getViewUri() throws HttpException { // TODO
	 * Auto-generated method stub return null; }
	 */
}
