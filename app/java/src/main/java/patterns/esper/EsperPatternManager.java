package patterns.esper;

import com.espertech.esper.common.client.EPCompiled;
import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.compiler.client.*;
import com.espertech.esper.runtime.client.*;

import cep.esper.EsperCEPEngine;
import schema.event.Event;
import schema.pattern.*;
import logger.PatternLogger;
import patterns.PatternManager;
import com.google.gson.*;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.*;
import java.util.logging.Logger;

/**
 * Manages the full lifecycle of pattern definitions within the Esper CEP engine.
 * 
 * This class handles loading pattern specifications from JSON, compiling and
 * deploying them into the Esper runtime, and logging detected matches as
 * {@link schema.pattern.PatternRecord} instances. It supports both atomic and
 * complex patterns, enabling hierarchical event detection where higher-level
 * patterns consume streams of lower-level matches.
 */


public class EsperPatternManager extends PatternManager<EsperCEPEngine> {
    private static final Logger LOG = Logger.getLogger(EsperPatternManager.class.getName());

    private final PatternLogger patternLogger;
    private final EPCompiler compiler = EPCompilerProvider.getCompiler();
    private List<PatternDef> patterns;

    public EsperPatternManager(EsperCEPEngine engine, PatternLogger logger) {
        super(engine);
        this.patternLogger = logger;
    }

    /**
     * Represents a pattern definition loaded from JSON, including its EPL query,
     * type (atomic or complex), and confidence aggregation rule.
     */
    private static class PatternDef {
        String name, epl, type;
        ConfidenceRule confidence;
        PatternDef(String n, String e, String t, ConfidenceRule c) {
            name=n; epl=e; type=t; confidence=c;
        }
    }
    
    /**
     * Defines how a pattern’s overall confidence should be calculated and thresholded.
     */
    private static class ConfidenceRule {
        String method; double threshold;
        ConfidenceRule(String m,double t){method=m;threshold=t;}
    }

    @Override
    public void loadPatterns(String resource) throws Exception {
        Gson gson = new Gson();
        List<PatternDef> defs = new ArrayList<>();

        try (Reader reader = new InputStreamReader(
                getClass().getClassLoader().getResourceAsStream(resource))) {

            JsonArray arr = gson.fromJson(reader, JsonArray.class);
            for (JsonElement e : arr) {
                var o = e.getAsJsonObject();
                String name = o.get("name").getAsString();
                String epl  = o.get("epl").getAsString();
                String type = o.has("type") ? o.get("type").getAsString() : "atomic";
                var conf = o.getAsJsonObject("confidence");
                defs.add(new PatternDef(
                        name, epl, type,
                        new ConfidenceRule(conf.get("aggregation").getAsString(),
                                           conf.get("threshold").getAsDouble())));
            }
        }
        this.patterns = defs;
        LOG.info("[EsperPatternManager] Loaded " + defs.size() + " patterns");
    }

    /**
     * Compiles, deploys, and attaches listeners for each loaded pattern,
     * logging matches and forwards them into the pattern stream.
     */
    @Override
    public void deployPatterns() throws Exception {
        EPRuntime rt = engine.getRuntime();
        Configuration cfg = engine.getConfiguration();
        CompilerArguments args = new CompilerArguments(cfg);

        for (PatternDef def : patterns) {
            EPCompiled compiled = compiler.compile(def.epl, args);
            EPDeployment dep = rt.getDeploymentService().deploy(compiled);
            attachListener(def, dep, rt);
        }
    }

    
    /**
     * Attaches a listener to Esper statements to handle both atomic and complex pattern matches
     */
    private void attachListener(PatternDef def, EPDeployment dep, EPRuntime rt) {
        for (EPStatement stmt : dep.getStatements()) {
            stmt.addListener((newData, oldData, s, r) -> {
                if (newData == null || newData.length == 0) return;

                List<Event> events = new ArrayList<>();
                List<Pattern> subs = new ArrayList<>();

                for (String prop : newData[0].getEventType().getPropertyNames()) {
                    Object v = newData[0].get(prop);
                    if (v instanceof Event e) events.add(e);
                    else if (v instanceof Pattern pr) subs.add(pr);
                }

                Pattern rec;
                if (def.type.equals("atomic")) {
                    double c = aggregate(events.stream().map(Event::getConfidence).toList(), def.confidence);
                    if (c < def.confidence.threshold) return;
                    rec = new AtomicPattern(def.name, events, c);
                } else {
                    double c = aggregate(subs.stream().map(Pattern::getConfidence).toList(), def.confidence);
                    if (c < def.confidence.threshold) return;
                    rec = new ComplexPattern(def.name, subs);
                    rec.confidence = c;
                }

                patternLogger.log(rec);
                rt.getEventService().sendEventBean(rec, "PatternRecordStream");
                LOG.info("[CEP] Fired " + def.type + " " + def.name + " | conf=" + rec.confidence);
            });
        }
    }

    /**
     * Aggregates confidence values according to the selected method (e.g., avg, min, max).
     */
    private double aggregate(List<Double> v, ConfidenceRule r){
        if (v.isEmpty()) return 0.0;
        return switch (r.method) {
            case "min" -> v.stream().mapToDouble(d->d).min().orElse(0.0);
            case "max" -> v.stream().mapToDouble(d->d).max().orElse(0.0);
            case "avg" -> v.stream().mapToDouble(d->d).average().orElse(0.0);
            case "most_recent" -> v.get(v.size() - 1);
            default -> v.stream().mapToDouble(d -> d).average().orElse(0.0);
        };
    }
}
