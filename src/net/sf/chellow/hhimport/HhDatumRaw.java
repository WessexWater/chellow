package net.sf.chellow.hhimport;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;

public class HhDatumRaw {
	private String core;

	private boolean isImport;

	private boolean isKwh;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatumRaw(String core, String endDateStr, String isImport, String isKwh,
			 String value, String statusStr)
			throws HttpException {
		Character status = null;
		if (statusStr != null) {
			statusStr = statusStr.trim();
			int statusLen = statusStr.length();
			if (statusLen == 1) {
				status = statusStr.charAt(0);
			} else if (statusLen > 1) {
				throw new UserException(
						"The status must be blank or a single character.");
			}
		}
		init(core, Boolean.parseBoolean(isImport), Boolean.parseBoolean(isKwh),
				new HhEndDate(endDateStr), Float.parseFloat(value), status);
	}

	public HhDatumRaw(String core, boolean isImport, boolean isKwh,
			HhEndDate endDate, float value, Character status)
			throws HttpException {
		init(core, isImport, isKwh, endDate, value, status);
	}

	private void init(String core, boolean isImport, boolean isKwh,
			HhEndDate endDate, float value, Character status)
			throws HttpException {
		this.core = core;
		this.isImport = isImport;
		this.isKwh = isKwh;
		this.endDate = endDate;
		this.value = value;
		this.status = status;
	}

	public String getMpanCore() {
		return core;
	}

	public boolean getIsImport() {
		return isImport;
	}

	public boolean getIsKwh() {
		return isKwh;
	}

	public HhEndDate getEndDate() {
		return endDate;
	}

	public float getValue() {
		return value;
	}

	public Character getStatus() {
		return status;
	}

	public String toString() {
		return "MPAN core: " + core + ", Is import? " + isImport + ", Is Kwh? "
				+ isKwh + ", End date " + endDate + ", Value " + value
				+ ", Status " + status;
	}
}
