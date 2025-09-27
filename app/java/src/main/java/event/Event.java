package event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Event {
    // Core fields
    @JsonProperty("stream_id")
    private String streamId;

    @JsonProperty("event_id")
    private String eventId;

    @JsonProperty("sampled_ts")
    private Double sampledTs;

    @JsonProperty("arrival_ts")
    private Double arrivalTs;

    @JsonProperty("event_ts")
    private Double eventTs;

    @JsonProperty("datatype")
    private String datatype;

    @JsonProperty("unit")
    private String unit;

    @JsonProperty("origin")
    private String origin;

    @JsonProperty("value")
    private Double value;

    // Reconstruction fields
    @JsonProperty("reconstructed_value")
    private Double reconstructedValue;

    @JsonProperty("reconstruction_method")
    private String reconstructionMethod;

    @JsonProperty("confidence")
    private Double confidence;

    @JsonProperty("reconstruction_flag")
    private Boolean reconstructionFlag;

    // Metadata
    @JsonProperty("status")
    private String status;

    @JsonProperty("source")
    private String source;

    @JsonProperty("extras")
    private Map<String, Object> extras;

    // --- Constructors ---
    public Event() {}

    public Event(String streamId, String eventId, Double sampledTs, Double value,
                 String datatype, String unit, String origin, String status,
                 String source, Map<String, Object> extras) {
        this.streamId = streamId;
        this.eventId = eventId;
        this.sampledTs = sampledTs;
        this.value = value;
        this.datatype = datatype;
        this.unit = unit;
        this.origin = origin;
        this.status = status;
        this.source = source;
        this.extras = extras;
    }

    // --- Getters and Setters ---
    public String getStreamId() { return streamId; }
    public void setStreamId(String streamId) { this.streamId = streamId; }

    public String getEventId() { return eventId; }
    public void setEventId(String eventId) { this.eventId = eventId; }

    public Double getSampledTs() { return sampledTs; }
    public void setSampledTs(Double sampledTs) { this.sampledTs = sampledTs; }

    public Double getArrivalTs() { return arrivalTs; }
    public void setArrivalTs(Double arrivalTs) { this.arrivalTs = arrivalTs; }

    public Double getEventTs() { return eventTs; }
    public void setEventTs(Double eventTs) { this.eventTs = eventTs; }

    public String getDatatype() { return datatype; }
    public void setDatatype(String datatype) { this.datatype = datatype; }

    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }

    public String getOrigin() { return origin; }
    public void setOrigin(String origin) { this.origin = origin; }

    public Double getValue() { return value; }
    public void setValue(Double value) { this.value = value; }

    public Double getReconstructedValue() { return reconstructedValue; }
    public void setReconstructedValue(Double reconstructedValue) { this.reconstructedValue = reconstructedValue; }

    public String getReconstructionMethod() { return reconstructionMethod; }
    public void setReconstructionMethod(String reconstructionMethod) { this.reconstructionMethod = reconstructionMethod; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public Boolean getReconstructionFlag() { return reconstructionFlag; }
    public void setReconstructionFlag(Boolean reconstructionFlag) { this.reconstructionFlag = reconstructionFlag; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public Map<String, Object> getExtras() { return extras; }
    public void setExtras(Map<String, Object> extras) { this.extras = extras; }

    // --- toString for debugging/logging ---
    @Override
    public String toString() {
        return "Event{" +
                "streamId='" + streamId + '\'' +
                ", eventId='" + eventId + '\'' +
                ", sampledTs=" + sampledTs +
                ", arrivalTs=" + arrivalTs +
                ", eventTs=" + eventTs +
                ", datatype='" + datatype + '\'' +
                ", unit='" + unit + '\'' +
                ", origin='" + origin + '\'' +
                ", value=" + value +
                ", reconstructedValue=" + reconstructedValue +
                ", reconstructionMethod='" + reconstructionMethod + '\'' +
                ", confidence=" + confidence +
                ", reconstructionFlag=" + reconstructionFlag +
                ", status='" + status + '\'' +
                ", source='" + source + '\'' +
                ", extras=" + extras +
                '}';
    }
}
