/**
 * UTSS Validation utilities
 */

import Ajv from "ajv";
import { parse as parseYAML } from "yaml";
import type { Strategy } from "./index";
import schema from "../../schema/v2/strategy.schema.json";

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

export class ValidationError extends Error {
  constructor(
    message: string,
    public errors: Array<{ path: string; message: string }>
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

export interface ValidationResult {
  valid: boolean;
  errors: Array<{ path: string; message: string }>;
  strategy?: Strategy;
}

/**
 * Validate a strategy object against the UTSS schema
 */
export function validateStrategy(strategy: unknown): ValidationResult {
  const valid = validate(strategy);

  if (!valid) {
    const errors = (validate.errors || []).map((err) => ({
      path: err.instancePath || "/",
      message: err.message || "Unknown error",
    }));

    return { valid: false, errors };
  }

  return { valid: true, errors: [], strategy: strategy as Strategy };
}

/**
 * Parse and validate a YAML string
 */
export function validateYAML(yamlContent: string): ValidationResult {
  let parsed: unknown;

  try {
    parsed = parseYAML(yamlContent);
  } catch (err) {
    return {
      valid: false,
      errors: [
        {
          path: "/",
          message: `YAML parse error: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ],
    };
  }

  return validateStrategy(parsed);
}
