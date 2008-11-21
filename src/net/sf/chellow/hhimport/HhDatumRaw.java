package net.sf.chellow.hhimport;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhDatum;
import net.sf.chellow.physical.HhEndDate;

public class HhDatumRaw {
	
	public static Character checkStatus(Character status) throws HttpException {
		if (status != null
				&& !(status.equals(HhDatum.ESTIMATE) || status.equals(HhDatum.ACTUAL))) {
			throw new UserException(
					"The status character must be E, A or null.");
		}
		return status;
	}

	private static Character checkStatus(String status) throws HttpException {
		if (status != null) {
			status = status.trim();
			if (status.length() > 1) {
				throw new UserException(
						"The status can only be a single character.");
			}
			Character statusCharacter = new Character(status.charAt(0));
			checkStatus(statusCharacter);
			return statusCharacter;
		} else {
			return null;
		}
	}

	private String core;

	private boolean isImport;

	private boolean isKwh;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatumRaw(String core, boolean isImport, boolean isKwh,
			HhEndDate endDate, float value, String status) throws HttpException {
		this(core, isImport, isKwh, endDate, value, checkStatus(status));
	}
	
	public HhDatumRaw(String core, boolean isImport, boolean isKwh,
			HhEndDate endDate, float value, Character status) throws HttpException {
		this.core = core;
		this.isImport = isImport;
		this.isKwh = isKwh;
		if (endDate == null) {
			throw new InternalException("The value 'endDate' must not be null.");
		}
		this.endDate = endDate;
		this.value = value;
		checkStatus(status);
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
