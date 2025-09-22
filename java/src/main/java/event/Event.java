package event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Event {
	public String stream_id;
    public double timestamp;
    public String datatype;
    public String unit;
    public Double value;
    public Double observed_value;
    public Double imputed_value;
    public String method;
    public Double confidence;
    public Map<String, Object> extras;

    // === Getters ===
    public String getStream_id() {
        return stream_id;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public String getDatatype() {
        return datatype;
    }

    public String getUnit() {
        return unit;
    }

    public Double getValue() {
        return value;
    }

    public Double getObserved_value() {
        return observed_value;
    }

    public Double getImputed_value() {
        return imputed_value;
    }

    public String getMethod() {
        return method;
    }

    public Double getConfidence() {
        return confidence;
    }

    public Map<String, Object> getExtras() {
        return extras;
    }

    // === Setters ===
    public void setStream_id(String stream_id) {
        this.stream_id = stream_id;
    }

    public void setTimestamp(double timestamp) {
        this.timestamp = timestamp;
    }

    public void setDatatype(String datatype) {
        this.datatype = datatype;
    }

    public void setUnit(String unit) {
        this.unit = unit;
    }

    public void setValue(Double value) {
        this.value = value;
    }

    public void setObserved_value(Double observed_value) {
        this.observed_value = observed_value;
    }

    public void setImputed_value(Double imputed_value) {
        this.imputed_value = imputed_value;
    }

    public void setMethod(String method) {
        this.method = method;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public void setExtras(Map<String, Object> extras) {
        this.extras = extras;
    }

    @Override
    public String toString() {
        return String.format(
            "Event(stream_id=%s, value=%s, method=%s, confidence=%s)",
            stream_id, value, method, confidence
        );
    }
}
