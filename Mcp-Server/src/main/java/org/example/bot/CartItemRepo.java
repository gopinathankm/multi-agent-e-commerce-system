package org.example.bot;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface CartItemRepo extends JpaRepository<CartItem, Long> {
    List<CartItem> findByProductId(Long productId);
}