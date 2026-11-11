package org.example.bot;

import java.util.List;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.stereotype.Service;

@Service
public class EcommerceToolService {

    private final ProductRepo productRepo;
    private final OrderRepo orderRepo;
    private final CartItemRepo cartItemRepo;

    public EcommerceToolService(ProductRepo productRepo, OrderRepo orderRepo, CartItemRepo cartItemRepo) {
        this.productRepo = productRepo;
        this.orderRepo = orderRepo;
        this.cartItemRepo = cartItemRepo;
    }

    @Tool(description = "Search products by name keyword")
    public List<Product> searchProducts(String query) {
        return productRepo.findByNameContainingIgnoreCase(query);
    }

    @Tool(description = "Check current stock quantity for a product by its ID")
    public String checkInventory(Long productId) {
        return productRepo.findById(productId)
                .map(p -> p.getName() + " has " + p.getStockQuantity() + " units in stock")
                .orElse("Product with ID " + productId + " not found");
    }

    @Tool(description = "Get the status and total amount of an order by order ID")
    public String getOrderStatus(Long orderId) {
        return orderRepo.findById(orderId)
                .map(o -> "Order #" + o.getId() + " for " + o.getCustomerName() +
                        " is " + o.getStatus() + ", total $" + o.getTotalAmount())
                .orElse("Order with ID " + orderId + " not found");
    }

    @Tool(description = "Add a product to the shopping cart. Requires productId and quantity.")
    public String addToCart(Long productId, int quantity) {
        return productRepo.findById(productId).map(product -> {
            List<CartItem> existing = cartItemRepo.findByProductId(productId);
            if (!existing.isEmpty()) {
                CartItem item = existing.get(0);
                item.setQuantity(item.getQuantity() + quantity);
                cartItemRepo.save(item);
            } else {
                cartItemRepo.save(new CartItem(productId, product.getName(), product.getPrice(), quantity));
            }
            return "Added " + quantity + " x " + product.getName() + " to cart.";
        }).orElse("Product with ID " + productId + " not found.");
    }

    @Tool(description = "View the current contents of the shopping cart.")
    public String viewCart() {
        List<CartItem> items = cartItemRepo.findAll();
        if (items.isEmpty()) {
            return "Your cart is empty.";
        }
        StringBuilder sb = new StringBuilder("Cart contents:\n");
        double total = 0;
        for (CartItem item : items) {
            sb.append("- ").append(item.getQuantity()).append(" x ").append(item.getProductName())
              .append(" @ $").append(item.getPrice()).append(" = $").append(item.getSubtotal()).append("\n");
            total += item.getSubtotal();
        }
        sb.append("Total: $").append(String.format("%.2f", total));
        return sb.toString();
    }

    @Tool(description = "Remove a product from the shopping cart by its productId.")
    public String removeFromCart(Long productId) {
        List<CartItem> items = cartItemRepo.findByProductId(productId);
        if (items.isEmpty()) {
            return "Product not found in cart.";
        }
        cartItemRepo.deleteAll(items);
        return "Removed product from cart.";
    }

    @Tool(description = "Checkout the current shopping cart. Creates a new order and clears the cart.")
    public String checkout() {
        List<CartItem> items = cartItemRepo.findAll();
        if (items.isEmpty()) {
            return "Your cart is empty. Nothing to checkout.";
        }
        double total = 0;
        for (CartItem item : items) {
            total += item.getSubtotal();
        }
        Order newOrder = new Order("Guest User", "PENDING", total);
        orderRepo.save(newOrder);
        cartItemRepo.deleteAll();
        return "Checkout successful! Created Order #" + newOrder.getId() + " for $" + String.format("%.2f", total) + ". Status: PENDING.";
    }
}