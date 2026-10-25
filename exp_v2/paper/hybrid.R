# exp_v2 paper figures for the hybrid (BM25 top k re-ranked by a tree kernel), ggplot2.
#
# usage: Rscript exp_v2/paper/hybrid.R
#   -> exp_v2/paper/figures/hybrid_rq1.pdf    replicate sets, mean over the five types: nP@5, nP@10, MRR, MAP (box plots)
#      exp_v2/paper/figures/hybrid_rq2.pdf    replicate sets, functional: nP@5, nP@10, MRR, MAP (box plots)
#      exp_v2/paper/figures/hybrid_full.pdf   every eligible query: value and 95% CI, RQ1 and RQ2 rows
# Inputs: exp_v2/results/hybrid/{replicate_values,full_values}.tsv (exp_v2/eval/hybrid.py).
# Box plots: geom_boxplot with its defaults, as in exp_v2/paper/figures.R. The full query set has one value per method,
# so it is shown as points with 95% CIs (bootstrap over functionalities).
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(dirname(here))
out <- file.path(here, "figures")
dir.create(out, showWarnings = FALSE)
R <- file.path(root, "exp_v2/results/hybrid")

kernels <- c("STK", "SSTK", "PTK")
kcol <- c("STK" = "#0072B2", "SSTK" = "#56B4E9", "PTK" = "#D55E00")
other <- c("BM25" = "#555555", "CodeBERT zs" = "#CC79A7", "CodeBERT ft" = "#009E73")
hows <- c("full ranking", "BM25 top 100", "BM25 top 200")

base_theme <- theme_classic(base_size = 8, base_family = "serif") +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey85"),
        axis.text = element_text(size = 7, colour = "black"), axis.line = element_line(linewidth = 0.3),
        axis.ticks = element_line(linewidth = 0.3), strip.background = element_blank(),
        strip.text = element_text(size = 8, face = "bold"), legend.text = element_text(size = 7),
        legend.title = element_text(size = 7), panel.spacing = unit(8, "pt"))
save <- function(p, name, w, h) {
  ggsave(file.path(out, name), p, width = w, height = h, units = "in", device = cairo_pdf)
  cat("figure", name, "\n")
}

# method label -> group on the x axis (kernel, or the baseline) and how the kernel ranks (full / top 100 / top 200)
classify <- function(d) {
  d |> mutate(
    group = case_when(grepl("^BM25→", method) ~ sub("^BM25→(\\w+) .*", "\\1", method), TRUE ~ method),
    how = case_when(grepl("k=100", method) ~ hows[2], grepl("k=200", method) ~ hows[3],
                    method %in% kernels ~ hows[1], TRUE ~ "baseline"))
}

# ---- replicate sets: box plots
rv <- read.delim(file.path(R, "replicate_values.tsv"), check.names = FALSE) |> classify()
n_seed <- n_distinct(rv$seed)
rep_plot <- function(measure_, metrics, name) {
  d <- rv |>
    filter(measure == measure_, metric %in% metrics) |>
    mutate(metric = factor(metric, levels = metrics),
           group = factor(group, levels = c(kernels, "BM25", "CodeBERT ft")),
           how = factor(how, levels = c(hows, "baseline")),
           fill = ifelse(how == "baseline", as.character(group), as.character(how)))
  fills <- c("full ranking" = "grey50", "BM25 top 100" = "grey85", "BM25 top 200" = "white", other)   # greys: ranking mode
  p <- ggplot(d, aes(x = group, y = value, fill = fill, group = interaction(group, how))) +
    geom_boxplot(position = position_dodge(width = 0.85, preserve = "single"), width = 0.75, linewidth = 0.25,
                 colour = "black", outlier.size = 0.5, outlier.stroke = 0.3, median.colour = "black",
                 median.linewidth = 0.4, key_glyph = "polygon") +
    geom_vline(xintercept = 3.5, linewidth = 0.2, colour = "grey60", linetype = "dashed") +
    facet_wrap(~metric, nrow = 2, scales = "free_y") +
    scale_fill_manual(values = fills, breaks = hows, name = "Tree kernel:") +
    labs(x = NULL, y = sprintf("value over %d replicate query sets", n_seed)) +
    guides(fill = guide_legend(nrow = 1, keywidth = unit(7, "pt"), keyheight = unit(7, "pt"))) +
    base_theme + theme(legend.position = "top", legend.margin = margin(0, 0, -4, 0))
  save(p, name, 7.0, 4.0)
}
rep_plot("mean5", c("nP@5", "nP@10", "MRR", "MAP"), "hybrid_rq1.pdf")
rep_plot("functional", c("nP@5", "nP@10", "MRR", "MAP"), "hybrid_rq2.pdf")

# ---- full query set: points with 95% CIs
fv <- read.delim(file.path(R, "full_values.tsv"), check.names = FALSE) |>
  filter(measure %in% c("mean5", "functional"), metric != "MAP@R") |>   # MAP@R: raw results only
  classify() |>
  mutate(panel = factor(paste(ifelse(measure == "mean5", "RQ1", "RQ2"), metric),
                        levels = c(paste("RQ1", c("nP@5", "nP@10", "MRR", "MAP")), paste("RQ2", c("nP@5", "nP@10", "MRR", "MAP")))),
         group = factor(group, levels = c("BM25", "CodeBERT zs", "CodeBERT ft", kernels)),
         how = factor(ifelse(how == "baseline", "baseline", how), levels = c("baseline", hows[2:3])))
shapes <- c("baseline" = 16, "BM25 top 100" = 1, "BM25 top 200" = 17)
p <- ggplot(fv, aes(x = group, y = value, colour = group, shape = how)) +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high), position = position_dodge(width = 0.6), size = 0.35,
                  linewidth = 0.35) +
  geom_vline(xintercept = 3.5, linewidth = 0.2, colour = "grey60", linetype = "dashed") +
  facet_wrap(~panel, nrow = 2, scales = "free_y") +
  scale_colour_manual(values = c(other, kcol), guide = "none") +
  scale_shape_manual(values = shapes, breaks = hows[2:3], name = "Tree kernel re-ranks:") +
  scale_x_discrete(labels = c("BM25", "CB zs", "CB ft", "BM25→STK", "BM25→SSTK", "BM25→PTK")) +
  labs(x = NULL, y = "value over all eligible queries (95% CI)") +
  base_theme + theme(legend.position = "top", legend.margin = margin(0, 0, -4, 0),
                     axis.text.x = element_text(size = 6, angle = 40, hjust = 1))
save(p, "hybrid_full.pdf", 7.0, 4.3)
