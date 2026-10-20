# RQ4 figures over the 10 replicate query sets (box plots, ggplot2).
#
# usage: Rscript paper/rq4_boxplots.R
#   -> paper/figures/rq4_fusion_replicates.pdf          fusion vs its components (RQ1: ST3, MT3, mean)
#      paper/figures/rq4_complementarity_replicates.pdf  share of relevant items found by PTK only / the other only / ...
# Inputs: results/replicates/per_replicate.tsv (eval/replicates.py), results/replicates/complementarity.tsv
# (eval/replicates_complementarity.py). Box = IQR and median, whiskers = min-max. Colours as in paper/make_assets.py.
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)
rdir <- file.path(root, "results/replicates")

box5 <- function(d, value, ...) {
  d |>
    group_by(...) |>
    summarise(ymin = min({{ value }}), lower = quantile({{ value }}, 0.25), middle = median({{ value }}),
              upper = quantile({{ value }}, 0.75), ymax = max({{ value }}), .groups = "drop")
}

base_theme <- theme_classic(base_size = 8, base_family = "serif") +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey85"),
        axis.text = element_text(size = 7, colour = "black"), axis.line = element_line(linewidth = 0.3),
        axis.ticks = element_line(linewidth = 0.3), strip.background = element_blank(),
        strip.text = element_text(size = 8), legend.text = element_text(size = 7))

# ---- fusion
pairs <- c("PTK + BM25", "PTK + CodeBERT ft")
roles <- c("tree kernel", "other", "weighted sum", "RRF")
fus <- read.delim(file.path(rdir, "per_replicate.tsv"), check.names = FALSE) |>
  pivot_longer(c(ST3, MT3, mean5), names_to = "measure", values_to = "map")
rows <- bind_rows(
  fus |> filter(method == "D PTK") |> mutate(pair = pairs[1], role = roles[1], fill = "PTK"),
  fus |> filter(method == "BM25") |> mutate(pair = pairs[1], role = roles[2], fill = "BM25"),
  fus |> filter(method == "PTK+BM25 wsum") |> mutate(pair = pairs[1], role = roles[3], fill = "fusion"),
  fus |> filter(method == "PTK+BM25 RRF") |> mutate(pair = pairs[1], role = roles[4], fill = "fusion"),
  fus |> filter(method == "D PTK") |> mutate(pair = pairs[2], role = roles[1], fill = "PTK"),
  fus |> filter(method == "CodeBERT ft") |> mutate(pair = pairs[2], role = roles[2], fill = "CodeBERT ft"),
  fus |> filter(method == "PTK+CodeBERT ft wsum") |> mutate(pair = pairs[2], role = roles[3], fill = "fusion"),
  fus |> filter(method == "PTK+CodeBERT ft RRF") |> mutate(pair = pairs[2], role = roles[4], fill = "fusion")
) |>
  mutate(measure = factor(recode(measure, mean5 = "Mean (5 types)"), levels = c("ST3", "MT3", "Mean (5 types)")),
         pair = factor(pair, levels = pairs),
         tick = factor(case_when(role == roles[1] ~ "PTK", role == roles[2] & fill == "BM25" ~ "BM25",
                                 role == roles[2] ~ "CB ft", role == roles[3] ~ "wsum", TRUE ~ "RRF"),
                       levels = c("PTK", "BM25", "CB ft", "wsum", "RRF")))
stats <- box5(rows, map, pair, measure, tick, fill)
fills <- c("PTK" = "#D55E00", "BM25" = "#555555", "CodeBERT ft" = "#009E73", "fusion" = "white")

p <- ggplot(stats, aes(x = tick, fill = fill)) +
  geom_boxplot(aes(ymin = ymin, lower = lower, middle = middle, upper = upper, ymax = ymax), stat = "identity",
               width = 0.6, linewidth = 0.25, colour = "black", median.colour = "black", median.linewidth = 0.5) +
  facet_wrap(~ pair + measure, nrow = 2, scales = "free_x", labeller = label_wrap_gen(width = 60, multi_line = FALSE)) +
  scale_fill_manual(values = fills, guide = "none") +
  labs(x = NULL, y = sprintf("MAP (%d query sets)", n_distinct(rows$seed))) +
  base_theme + theme(panel.spacing.x = unit(8, "pt"), panel.spacing.y = unit(6, "pt"))
ggsave(file.path(root, "paper/figures/rq4_fusion_replicates.pdf"), p, width = 7.0, height = 3.0, units = "in",
       device = cairo_pdf)
cat("figure rq4_fusion_replicates.pdf\n")

# ---- complementarity
parts <- c("found by both", "PTK only", "other only", "neither")
comp <- read.delim(file.path(rdir, "complementarity.tsv")) |>
  filter(set %in% c("ST3", "MT3", "functional")) |>
  mutate(total = both + ptk_only + other_only + neither) |>
  pivot_longer(c(both, ptk_only, other_only, neither), names_to = "part", values_to = "n") |>
  mutate(share = n / total,
         part = factor(recode(part, both = parts[1], ptk_only = parts[2], other_only = parts[3], neither = parts[4]),
                       levels = parts),
         set = factor(recode(set, functional = "functional (RQ2)"), levels = c("ST3", "MT3", "functional (RQ2)")),
         other = factor(paste("PTK vs", other), levels = c("PTK vs BM25", "PTK vs CodeBERT ft")))
cstats <- box5(comp, share, other, set, part)
cfill <- c("found by both" = "#999999", "PTK only" = "#D55E00", "other only" = "#333333", "neither" = "white")

dodge <- position_dodge(width = 0.85)
p <- ggplot(cstats, aes(x = set, fill = part)) +
  geom_boxplot(aes(ymin = ymin, lower = lower, middle = middle, upper = upper, ymax = ymax), stat = "identity",
               position = dodge, width = 0.75, linewidth = 0.3, colour = "black", median.colour = "black",
               median.linewidth = 0.5, key_glyph = "polygon") +
  facet_wrap(~other, nrow = 1) +
  scale_fill_manual(values = cfill, name = NULL) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1), expand = expansion(add = c(0, 0.01))) +
  labs(x = NULL, y = sprintf("relevant items in the top R\n(%d query sets)", n_distinct(comp$seed))) +
  base_theme + theme(legend.position = "top", legend.key.size = unit(7, "pt"), legend.margin = margin(0, 0, -4, 0))
ggsave(file.path(root, "paper/figures/rq4_complementarity_replicates.pdf"), p, width = 7.0, height = 2.4, units = "in",
       device = cairo_pdf)
cat("figure rq4_complementarity_replicates.pdf\n")
