/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2013 Wessex Water Services Limited
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

import java.math.BigDecimal;
import java.net.URI;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.List;

import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.jdbc.Work;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channels extends EntityList {
        public static final UriPathElement URI_ID;

        static {
                try {
                        URI_ID = new UriPathElement("channels");
                } catch (HttpException e) {
                        throw new RuntimeException(e);
                }
        }

        private Era era;

        public Channels(Era era) {
                this.era = era;
        }

        public UriPathElement getUriId() {
                return URI_ID;
        }

        public MonadUri getEditUri() throws HttpException {
                return era.getEditUri().resolve(getUriId()).append("/");
        }

        public void httpGet(Invocation inv) throws HttpException {
                inv.sendOk(document());
        }
        
        private Document document() throws HttpException {
                Document doc = MonadUtils.newSourceDocument();
                Element source = doc.getDocumentElement();
                Element channelsElement = toXml(doc);
                source.appendChild(channelsElement);
                channelsElement.appendChild(era.toXml(doc, new XmlTree("supply")));
                for (Channel channel : era.getChannels()) {
                        channelsElement.appendChild(channel.toXml(doc));
                }
                return doc;
        }

        public void httpPost(Invocation inv) throws HttpException {
                Hiber.setReadWrite();
                Boolean isImport = inv.getBoolean("is-import");
                Boolean isKwh = inv.getBoolean("is-kwh");
                if (!inv.isValid()) {
                        throw new UserException(document());
                }
                Channel channel = era.insertChannel(isImport, isKwh);
                Hiber.commit();
                inv.sendSeeOther(channel.getEditUri());
        }
        
        public Urlable getChild(UriPathElement uriId) throws HttpException {
                return (Channel) Hiber
                                .session()
                                .createQuery(
                                                "from Channel channel where channel.era = :era and channel.id = :channelId")
                                .setEntity("era", era).setLong("channelId",
                                                Long.parseLong(uriId.getString())).uniqueResult();
        }

        public Element toXml(Document doc) throws HttpException {
                return doc.createElement("channels");
        }

        @Override
        public URI getViewUri() throws HttpException {
                // TODO Auto-generated method stub
                return null;
        }
        
        static public class HhWork implements Work {
                private List<HhDatumRaw> dataRaw;
                private Channel channel;
                
                public HhWork(Channel channel, List<HhDatumRaw> dataRaw) {
                        this.dataRaw = dataRaw;
                        this.channel = channel;
                }
        
                @SuppressWarnings("unchecked")
                public void execute(Connection con) throws HttpException {
                        // long now = System.currentTimeMillis();
                        HhDatumRaw firstRawDatum = dataRaw.get(0);
                        HhDatumRaw lastRawDatum = dataRaw.get(dataRaw.size() - 1);
                        // Debug.print("First dr = " + firstRawDatum + " cond dr " +
                        // lastRawDatum);
                        List<HhDatum> data = (List<HhDatum>) Hiber
                                        .session()
                                        .createQuery(
                                                        "from HhDatum datum where datum.channel = :channel and "
                                                                        + "datum.startDate.date >= :startDate and datum.startDate.date <= :finishDate order by datum.startDate.date")
                                        .setEntity("channel", channel)
                                        .setTimestamp("startDate",
                                                        firstRawDatum.getStartDate().getDate())
                                        .setTimestamp("finishDate",
                                                        lastRawDatum.getStartDate().getDate()).list();
                        HhStartDate siteCheckFrom = null;
                        HhStartDate siteCheckTo = null;
                        HhStartDate notActualFrom = null;
                        HhStartDate notActualTo = null;
                        HhStartDate deleteMissingFrom = null;
                        HhStartDate deleteMissingTo = null;
                        HhStartDate lastAdditionDate = null;
                        HhStartDate prevStartDate = null;
                        int missing = 0;
                        BigDecimal originalDatumValue = new BigDecimal(0);
                        char originalDatumStatus = Character.UNASSIGNED;
                PreparedStatement stmt;
                try {
                        stmt = con
                                        .prepareStatement("INSERT INTO hh_datum VALUES (nextval('hh_datum_id_sequence'), ?, ?, ?, ?)");
                        Statement st = con.createStatement();
                                st.executeUpdate("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE");                    } catch (SQLException e1) {
                        throw new InternalException(e1);
                }
                int batchSize = 0;
                for (int i = 0; i < dataRaw.size(); i++) {
                        // Debug.print("Start processing hh: " + (System.currentTimeMillis()
                        // - now));
                        boolean added = false;
                        boolean altered = false;
                        HhDatumRaw datumRaw = dataRaw.get(i);
                        HhDatum datum = null;

                        if (i - missing < data.size()) {
                                datum = data.get(i - missing);
                                if (!datumRaw.getStartDate().equals(datum.getStartDate())) {
                                        datum = null;
                                }
                        }
                        if (datum == null) {
                                // Debug.print("About to save datum: "
                                // + (System.currentTimeMillis() - now));
                                try {
                                        stmt.setLong(1, channel.getId());

                                        stmt.setTimestamp(2, new Timestamp(datumRaw.getStartDate()
                                                        .getDate().getTime()));
                                        stmt.setBigDecimal(3, datumRaw.getValue());
                                        stmt.setString(4, Character.toString(datumRaw.getStatus()));
                                        stmt.addBatch();
                                        batchSize++;
                                } catch (SQLException e) {
                                        throw new InternalException(e);
                                }
                                // Debug.print("Saved datum: "
                                // + (System.currentTimeMillis() - now));
                                // Hiber.flush();
                                lastAdditionDate = datumRaw.getStartDate();
                                added = true;
                                missing++;
                                if (deleteMissingFrom == null) {
                                        deleteMissingFrom = datumRaw.getStartDate();
                                }
                                deleteMissingTo = datumRaw.getStartDate();
                                // Debug.print("Resolved missing: "
                                // + (System.currentTimeMillis() - now));
                        } else if (datumRaw.getValue().doubleValue() != datum.getValue()
                                        .doubleValue() || datumRaw.getStatus() != datum.getStatus()) {
                                // Debug.print("About to update datum: " + datum + " with " +
                                // datumRaw + " "
                                // + (System.currentTimeMillis() - now));
                                originalDatumValue = datum.getValue();
                                originalDatumStatus = datum.getStatus();
                                datum.update(datumRaw.getValue(), datumRaw.getStatus());
                                Hiber.flush();
                                altered = true;
                        }
                        // Debug.print("About to see if changed: "
                        // + (System.currentTimeMillis() - now));
                        if (added || altered) {
                                if (siteCheckFrom == null) {
                                        siteCheckFrom = datumRaw.getStartDate();
                                }
                                siteCheckTo = datumRaw.getStartDate();
                                if (datumRaw.getValue().doubleValue() < 0) {
                                        channel.addSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw.getStartDate(),
                                                        datumRaw.getStartDate());
                                } else if (altered && originalDatumValue.doubleValue() < 0) {
                                        channel.deleteSnag(ChannelSnag.SNAG_NEGATIVE,
                                                        datumRaw.getStartDate());
                                }
                                if (HhDatum.ACTUAL != datumRaw.getStatus()) {
                                        if (notActualFrom == null) {
                                                notActualFrom = datumRaw.getStartDate();
                                        }
                                        notActualTo = datumRaw.getStartDate();
                                } else if (altered && originalDatumStatus != HhDatum.ACTUAL) {
                                        channel.deleteSnag(ChannelSnag.SNAG_ESTIMATED,
                                                        datumRaw.getStartDate());
                                }
                        }
                        if (lastAdditionDate != null
                                        && (lastAdditionDate.equals(prevStartDate) || batchSize > 100)) {
                                // Debug.print("About to execute batch "
                                // + (System.currentTimeMillis() - now));
                                try {
                                        stmt.executeBatch();
                                        Statement st = con.createStatement();
                                        st.executeUpdate("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE");            
                                        // Debug.print("Added  lines.");
                                        batchSize = 0;
                                } catch (SQLException e) {
                                        throw new InternalException(e);
                                }
                                lastAdditionDate = null;
                        }
                        if (siteCheckTo != null && siteCheckTo.equals(prevStartDate)) {
                                // Debug.print("About to do site check: "
                                // + (System.currentTimeMillis() - now));
                                channel.siteCheck(siteCheckFrom, siteCheckTo);
                                siteCheckFrom = null;
                                siteCheckTo = null;
                                // Debug.print("Finished site check: "
                                // + (System.currentTimeMillis() - now));
                        }
                        if (notActualTo != null && notActualTo.equals(prevStartDate)) {
                                // Debug.print("Started not actual: "
                                // + (System.currentTimeMillis() - now));
                                channel.addSnag(ChannelSnag.SNAG_ESTIMATED, notActualFrom, notActualTo);
                                // Debug.print("Finished not actual: "
                                // + (System.currentTimeMillis() - now));
                                notActualFrom = null;
                                notActualTo = null;
                        }
                        if (deleteMissingTo != null
                                        && deleteMissingTo.equals(prevStartDate)) {
                                // Debug.print("Starting resolvedMissing: "
                                // + (System.currentTimeMillis() - now));
                                channel.deleteSnag(ChannelSnag.SNAG_MISSING, deleteMissingFrom,
                                                deleteMissingTo);
                                deleteMissingFrom = null;
                                deleteMissingTo = null;
                                // Debug.print("Finished resolveMissing: "
                                // + (System.currentTimeMillis() - now));
                        }
                        prevStartDate = datumRaw.getStartDate();
                }
                if (lastAdditionDate != null && lastAdditionDate.equals(prevStartDate)) {
                        // Debug.print("About to execute batch 2: "
                        // + (System.currentTimeMillis() - now));
                        try {
                                stmt.executeBatch();
                                Statement st = con.createStatement();
                                st.executeUpdate("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE");
                        } catch (SQLException e) {
                                throw new InternalException(e);
                        }
                        lastAdditionDate = null;
                }
                if (siteCheckTo != null && siteCheckTo.equals(prevStartDate)) {
                        // Debug.print("About to start site thing 2: "
                        // + (System.currentTimeMillis() - now));
                        channel.siteCheck(siteCheckFrom, siteCheckTo);
                        // Debug.print("About to finish site thing 2: "
                        // + (System.currentTimeMillis() - now));
                }
                if (notActualTo != null && notActualTo.equals(prevStartDate)) {
                        // Debug.print("About to start not actual 2: "
                        // + (System.currentTimeMillis() - now));
                        channel.addSnag(ChannelSnag.SNAG_ESTIMATED, notActualFrom, notActualTo);
                        // Debug.print("About to finsih not actual 2: "
                        // + (System.currentTimeMillis() - now));
                }
                if (deleteMissingTo != null && deleteMissingTo.equals(prevStartDate)) {
                        // Debug.print("About to start resolvem 2: "
                        // + (System.currentTimeMillis() - now));
                        channel.deleteSnag(ChannelSnag.SNAG_MISSING, deleteMissingFrom,
                                        deleteMissingTo);
                        // Debug.print("About to finish resolvem 2: "
                        // + (System.currentTimeMillis() - now));
                }
                // Debug.print("Finished method 2: " + (System.currentTimeMillis() -
                // now));
        }
        }
}