package patterns;

import cep.CEPEngine;

/**
 * Manages the full lifecycle of pattern handling
 */
public abstract class PatternManager<T extends CEPEngine> {

    protected final T engine;

    public PatternManager(T engine) {
        this.engine = engine;
    }

    /**
     * Load pattern definitions (from file, API, DB, etc.).
     * @param source Identifier for the pattern source (e.g., filename or URL).
     */
    public abstract void loadPatterns(String source) throws Exception;

    /**
     * Deploy loaded patterns to the CEP engine runtime and attach listeners
     */
    public abstract void deployPatterns() throws Exception;

    
    public void initialize(String source) throws Exception {
        loadPatterns(source);
        deployPatterns();
    }
}
